# ================================================================
#  love_v4.assistant.controller  (v4.2 — two-stage wake engine)
#  ----------------------------------------------------------------
#  What changed from v4.1
#  ----------------------
#  * Removed the monolithic _continuous_loop() that called
#    recognize_google on every iteration whether awake or asleep.
#  * Replaced with VoicePipeline (assistant/utils/wake_engine.py):
#      - WakeThread:   lightweight 3-second clips, string matching only
#      - CommandThread: activated per wake cycle, full-length capture
#  * Controller no longer owns a Listener directly for the main loop;
#    VoicePipeline owns both recognisers and the shared Microphone.
#  * A separate Listener is still available via self.listener for
#    one-shot use (e.g. type_command does not need it, kept for API
#    compatibility with external code that may call it directly).
#  * All public methods (start_listening, stop, respond, type_command)
#    have identical signatures — the UI layer is NOT changed.
#
#  State machine
#  -------------
#    SLEEPING   <- waiting for wake word (VoicePipeline._wake_loop)
#    ACTIVE     <- wake word heard, command window open
#    PROCESSING <- command dispatched to router
#    ACTIVE     <- back to command window (stays awake)
#    SLEEPING   <- stop word heard or stop() called
#
#  Thread map
#  ----------
#    love-calibrate  : startup only, exits after ~1 s
#    love-wake       : permanent daemon, owns WakeThread logic
#    (inline)        : CommandThread runs inline on love-wake to
#                      prevent TTS echo-triggering wake detection
# ================================================================

from __future__ import annotations

import threading
import webbrowser
from enum import Enum, auto
from typing import Callable, Optional

# love_core imports
from love_core.voice.listen      import Listener
from love_core.voice.speak       import Speaker
from love_core.command_registry  import CommandRegistry
from love_core.router            import Router, DispatchStatus
from love_core.memory.session    import SessionMemory
from love_core.commands          import browser, apps, system
from love_core.utils.logger      import get_logger

# love_v4 command modules
from assistant.commands import close_commands, extended_browser

# love_v4 utilities
from assistant.utils.app_launcher import WindowsAppLauncher
from assistant.utils.wake_engine  import VoicePipeline

log = get_logger("love_v4.controller")


# ── Wake / Stop word lists ────────────────────────────────────
WAKE_WORDS: list[str] = [
    "hey love",
    "hello love",
    "love",
]

STOP_WORDS: list[str] = [
    "bye love",
    "sleep love",
    "stop love",
]


# ── States ────────────────────────────────────────────────────

class AssistantState(Enum):
    SLEEPING   = auto()   # idle, waiting for wake word
    ACTIVE     = auto()   # awake, command window open
    PROCESSING = auto()   # executing a dispatched command
    # Legacy aliases — keeps UI code compiled against v4.0/v4.1 working
    IDLE       = SLEEPING
    LISTENING  = ACTIVE


# ── Controller ───────────────────────────────────────────────

class AssistantController:
    """
    Orchestrates the two-stage voice pipeline, command routing,
    and UI feedback for love_v4.

    Public interface is unchanged from v4.0 and v4.1.

    Parameters
    ----------
    on_user_message : callback(text: str)
    on_love_message : callback(text: str)
    on_state_change : callback(state: AssistantState)
    on_error        : callback(msg: str)
    """

    def __init__(
        self,
        on_user_message  : Callable[[str], None],
        on_love_message  : Callable[[str], None],
        on_state_change  : Callable[[AssistantState], None],
        on_error         : Callable[[str], None],
    ) -> None:
        self._on_user  = on_user_message
        self._on_love  = on_love_message
        self._on_state = on_state_change
        self._on_error = on_error

        self._state                          = AssistantState.SLEEPING
        self._pending_app_name: Optional[str] = None

        # ── love_core components ──────────────────────────────
        self.registry = CommandRegistry("love_v4")
        self.router   = Router(registry=self.registry)
        self.memory   = SessionMemory(max_entries=100)
        self.speaker  = Speaker(rate=175, volume=1.0)

        # Listener kept for API compatibility / direct use
        self.listener = Listener(language="en-US", timeout=6, phrase_limit=10)

        # ── Utilities ────────────────────────────────────────
        self.launcher = WindowsAppLauncher(speak_fn=self.respond)

        # ── Two-stage pipeline ───────────────────────────────
        self.pipeline = VoicePipeline(
            wake_words   = WAKE_WORDS,
            stop_words   = STOP_WORDS,
            on_wake      = self._on_pipeline_wake,
            on_command   = self._on_pipeline_command,
            on_stop_word = self._on_pipeline_stop,
            on_error     = self._on_error,
        )

        self._setup_registry()
        self._setup_router()

        log.info("AssistantController v4.2 ready. Registry: %s", self.registry)

    # ── Setup ─────────────────────────────────────────────────

    def _setup_registry(self) -> None:
        browser.register_all(registry=self.registry)
        apps.register_all(registry=self.registry)
        system.register_all(registry=self.registry)
        close_commands.register_all(registry=self.registry)
        extended_browser.register_all(registry=self.registry)

        self.registry.register("yes",  self._confirm_yes,  tags=["conversation"])
        self.registry.register("no",   self._confirm_no,   tags=["conversation"])
        self.registry.register("help", self._show_help,    tags=["meta"])

        self.registry.register(
            "open",
            self._open_app,
            is_prefix   = True,
            description = "Open any application by name.",
            tags        = ["apps"],
            override    = True,
        )

        self._patch_command_speak()
        log.debug("Registry loaded: %d commands", len(self.registry))

    def _patch_command_speak(self) -> None:
        """Route all love_core command output through self.respond()."""
        import love_core.voice.speak as speak_module
        speak_module._default_speaker = self.speaker

        import love_core.commands.system as sys_mod

        def _tell_time():
            from love_core.commands.system import get_time
            self.respond(f"The time is {get_time()}")

        def _tell_date():
            from love_core.commands.system import get_date
            self.respond(f"Today is {get_date()}")

        sys_mod.tell_time = _tell_time
        sys_mod.tell_date = _tell_date
        for phrase in ("time", "what time is it", "what's the time"):
            self.registry.register(phrase, _tell_time, override=True)
        for phrase in ("date", "what's the date", "what day is it"):
            self.registry.register(phrase, _tell_date, override=True)

    def _setup_router(self) -> None:
        def fallback(text: str) -> None:
            self.respond("I didn't understand that. Try saying 'help'.")
            self.memory.record(text, resolved=False)
        self.router.set_fallback(fallback)

    # ── Public API (unchanged signatures) ────────────────────

    def start_listening(self) -> None:
        """
        Start the two-stage voice pipeline.
        Calibrates the microphone (once), then runs WakeThread.
        Safe to call multiple times.
        """
        self.pipeline.start()
        log.info("Pipeline started via start_listening().")

    def stop(self) -> None:
        """Stop the pipeline and return to SLEEPING state."""
        self.pipeline.stop()
        self._set_state(AssistantState.SLEEPING)
        log.info("Pipeline stopped.")

    def respond(self, text: str) -> None:
        """Deliver a response to UI + TTS. Thread-safe."""
        log.info("LOVE: %s", text)
        self._on_love(text)
        self.speaker.speak(text)

    def type_command(self, text: str) -> None:
        """
        Process a keyboard-typed command.
        Bypasses wake word — routes directly to the registry.
        """
        if not text.strip():
            return
        self._on_user(text)
        self._set_state(AssistantState.PROCESSING)
        self._dispatch(text.lower().strip())
        self._set_state(AssistantState.SLEEPING)

    # ── Pipeline callbacks ────────────────────────────────────
    # These are called from VoicePipeline's daemon threads.
    # They must not block for long (TTS speak() is acceptable
    # because the wake loop is paused during command capture).

    def _on_pipeline_wake(self) -> None:
        """Called by VoicePipeline when a wake word is detected."""
        self._on_user("hey love")   # echo to UI for clarity
        self._set_state(AssistantState.ACTIVE)
        self.respond("I'm listening.")

    def _on_pipeline_command(self, text: str) -> None:
        """Called by VoicePipeline with a captured command phrase."""
        self._on_user(text)
        self._set_state(AssistantState.PROCESSING)
        self._dispatch(text)
        self._set_state(AssistantState.ACTIVE)   # stay awake after command

    def _on_pipeline_stop(self) -> None:
        """Called by VoicePipeline when a stop word is detected."""
        self._on_user("bye love")
        self.respond("Going to sleep. Say 'hey love' to wake me.")
        self._set_state(AssistantState.SLEEPING)

    # ── Command dispatch ──────────────────────────────────────

    def _dispatch(self, utterance: str) -> None:
        """Route *utterance* through the registry and record in memory."""
        result = self.router.dispatch(utterance)
        self.memory.record(utterance, resolved=result.matched)
        if result.status == DispatchStatus.ERROR and result.error:
            self.respond(f"Something went wrong: {result.error}")

    # ── App launcher ──────────────────────────────────────────

    def _open_app(self, app_name: str) -> None:
        """Prefix-command handler for 'open <x>'."""
        app_name = app_name.strip()
        if not app_name:
            self.respond("Open which application?")
            return

        _BROWSER_TARGETS: dict[str, str] = {
            "youtube":   "https://www.youtube.com",
            "google":    "https://www.google.com",
            "github":    "https://www.github.com",
            "gmail":     "https://mail.google.com",
            "reddit":    "https://www.reddit.com",
        }
        if app_name in _BROWSER_TARGETS:
            webbrowser.open(_BROWSER_TARGETS[app_name])
            self.respond(f"Opening {app_name.title()}.")
            return

        if self.launcher.launch(app_name):
            self.respond(f"Opening {app_name}.")
            return

        # Not found — offer web fallback
        web_url = self.launcher.web_fallback_url(app_name)
        self._pending_app_name = app_name

        if web_url:
            self.respond(
                f"{app_name.title()} is not installed. "
                f"Should I open the web version?"
            )
            self.memory.record(
                f"open {app_name}",
                resolved = False,
                context  = "not installed",
                app_name = app_name,
                web_url  = web_url,
            )
        else:
            self.respond(
                f"I couldn't find {app_name}. "
                f"It may not be installed on this machine."
            )
            self._pending_app_name = None

    # ── Conversation commands ─────────────────────────────────

    def _confirm_yes(self) -> None:
        if self._pending_app_name:
            app_name = self._pending_app_name
            web_url  = self.launcher.web_fallback_url(app_name)
            self._pending_app_name = None
            if web_url:
                webbrowser.open(web_url)
                self.respond(f"Opening {app_name.title()} in the browser.")
                return
        self.respond("Okay!")

    def _confirm_no(self) -> None:
        self._pending_app_name = None
        self.respond("Alright, no problem.")

    def _show_help(self) -> None:
        lines = [
            "hey love          -> wake me up",
            "bye love          -> go to sleep",
            "open youtube / open google / open vscode",
            "search <query>",
            "close chrome / close notepad",
            "new tab / close tab",
            "time / date",
            "volume up / volume down / mute",
            "screenshot",
        ]
        self.respond("Here are some things I can do:")
        for line in lines:
            self._on_love(f"  * {line}")

    # ── Helpers ───────────────────────────────────────────────

    def _set_state(self, state: AssistantState) -> None:
        self._state = state
        self._on_state(state)
