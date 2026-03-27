# ================================================================
#  love_v4.assistant.utils.wake_engine  (v4.4 — Porcupine + Whisper)
#  ----------------------------------------------------------------
#  Drop-in replacement for the SpeechRecognition-based v4.2 engine.
#  The VoicePipeline class preserves the EXACT same constructor
#  signature so controller.py needs ZERO changes.
#
#  v4.2 (SpeechRecognition)         v4.4 (Porcupine + Whisper)
#  ────────────────────────────────────────────────────────────
#  WakeThread: recognize_google()   WakeThread: porcupine.process_frame()
#  CommandThread: recognize_google  CommandThread: whisper.record_and_transcribe()
#  Cloud-dependent                  100% offline
#  ~200-500 ms wake latency         ~32 ms wake latency (one frame)
#  ~1-3 s command latency           ~50-150 ms command latency
#
#  Thread model
#  ────────────
#
#    love-wake (daemon, permanent)
#    │
#    │   loop:
#    │     porcupine.process_frame()   <- ~32 ms per iteration
#    │     if detected:
#    │       call on_wake()
#    │       spawn love-cmd thread
#    │       wait for love-cmd to finish   <- blocks wake loop during command
#    │                                        prevents TTS echo-triggering
#    │
#    └──► love-cmd (daemon, per-wake-cycle)
#              whisper.record_and_transcribe()
#              if stop word: call on_stop_word()
#              else:         call on_command(text)
#
#  The wake loop is paused during command capture (love-cmd runs
#  sequentially, not concurrently with love-wake).  This is
#  intentional: it prevents the assistant's own TTS output from
#  triggering another wake event.
#
#  Constructor interface (unchanged from v4.2)
#  ───────────────────────────────────────────
#      VoicePipeline(
#          wake_words   = [...],   # unused — Porcupine handles this via .ppn
#          stop_words   = [...],   # checked against Whisper output
#          on_wake      = callable,
#          on_command   = callable(text),
#          on_stop_word = callable,
#          on_error     = callable(msg),
#      )
#
#  Configuration
#  ─────────────
#  Set the Picovoice access key and model path via environment
#  variables or pass a PipelineConfig object:
#
#      PICOVOICE_ACCESS_KEY  = "your-key"
#      LOVE_KEYWORD_PATH     = "models/hey-love_windows.ppn"
#      LOVE_WHISPER_MODEL    = "base.en"   (optional, default base.en)
#
#  Requirements
#  ────────────
#    pip install pvporcupine sounddevice faster-whisper numpy
# ================================================================

from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field
from typing import Callable, Optional

from love_core.utils.logger import get_logger
from assistant.utils.porcupine_listener import PorcupineListener
from assistant.utils.whisper_listener   import WhisperListener

log = get_logger("love_v4.wake_engine")


# ── Configuration ─────────────────────────────────────────────

@dataclass
class PipelineConfig:
    """
    All tunable settings for VoicePipeline.

    Can be built from environment variables via PipelineConfig.from_env()
    or constructed directly.
    """
    # Picovoice
    access_key      : str   = ""
    keyword_path    : str   = os.path.join("models", "hey-love_windows.ppn")
    builtin_keyword : str   = "porcupine"   # fallback if .ppn is missing
    porcupine_sensitivity : float = 0.5

    # Whisper
    whisper_model   : str   = "base.en"
    whisper_device  : str   = "cpu"
    whisper_compute : str   = "int8"
    max_record_secs : float = 8.0

    # Audio device
    input_device    : Optional[int] = None   # None = system default

    @classmethod
    def from_env(cls) -> "PipelineConfig":
        """
        Build config from environment variables.

        Variables
        ---------
        PICOVOICE_ACCESS_KEY   : required
        LOVE_KEYWORD_PATH      : path to .ppn (optional, has default)
        LOVE_WHISPER_MODEL     : e.g. "base.en", "small.en" (optional)
        """
        return cls(
            access_key    = os.environ.get("PICOVOICE_ACCESS_KEY", ""),
            keyword_path  = os.environ.get(
                "LOVE_KEYWORD_PATH",
                os.path.join("models", "hey-love_windows.ppn"),
            ),
            whisper_model = os.environ.get("LOVE_WHISPER_MODEL", "base.en"),
        )


# ── Pipeline ──────────────────────────────────────────────────

class VoicePipeline:
    """
    Two-stage offline voice pipeline: Porcupine wake word + Whisper STT.

    Drop-in replacement for the v4.2 SpeechRecognition pipeline.
    Constructor signature is IDENTICAL to v4.2 VoicePipeline.

    Parameters
    ----------
    wake_words    : list[str]
        Kept for API compatibility.  Wake word detection is handled by
        Porcupine via the .ppn file; this list is not used for matching
        but is logged for debugging.
    stop_words    : list[str]
        Phrases that put the assistant back to sleep.  Checked against
        Whisper output with simple string membership.
    on_wake       : Callable[[], None]
        Called immediately when Porcupine detects the wake word.
    on_command    : Callable[[str], None]
        Called with the Whisper transcription of the user's command.
    on_stop_word  : Callable[[], None]
        Called when Whisper output contains a stop word.
    on_error      : Callable[[str], None]
        Called with an error message on non-fatal failures.
    config        : PipelineConfig | None
        Hardware/model settings.  If None, reads from environment variables.
    """

    def __init__(
        self,
        wake_words    : list[str],
        stop_words    : list[str],
        on_wake       : Callable[[], None],
        on_command    : Callable[[str], None],
        on_stop_word  : Callable[[], None],
        on_error      : Callable[[str], None],
        config        : Optional[PipelineConfig] = None,
    ) -> None:
        self._wake_words  = [w.lower().strip() for w in wake_words]
        self._stop_words  = [w.lower().strip() for w in stop_words]
        self._on_wake     = on_wake
        self._on_command  = on_command
        self._on_stop     = on_stop_word
        self._on_error    = on_error
        self._cfg         = config or PipelineConfig.from_env()

        # Thread control
        self._exit_event  = threading.Event()
        self._cmd_done    = threading.Event()   # love-wake waits on this
        self._wake_thread : Optional[threading.Thread] = None

        # Audio components — created lazily in start()
        self._porcupine  : Optional[PorcupineListener] = None
        self._whisper    : Optional[WhisperListener]   = None
        self._initialised = False

        log.info(
            "VoicePipeline v4.4 created. wake_words=%s stop_words=%s",
            self._wake_words, self._stop_words,
        )

    # ── Public API (unchanged from v4.2) ──────────────────────

    def start(self) -> None:
        """
        Initialise audio engines and start WakeThread.
        Safe to call multiple times (idempotent).
        """
        if self._wake_thread and self._wake_thread.is_alive():
            log.debug("Pipeline already running.")
            return

        self._exit_event.clear()
        self._cmd_done.clear()

        # Initialise in a background thread so the UI is not blocked
        # during model loading (~1-3 s for Whisper base.en)
        threading.Thread(
            target = self._init_and_start,
            daemon = True,
            name   = "love-init",
        ).start()

    def stop(self) -> None:
        """Signal all threads to exit and release audio resources."""
        log.info("VoicePipeline stop requested.")
        self._exit_event.set()
        self._cmd_done.set()   # unblock _wait_for_command if running

        if self._porcupine is not None:
            self._porcupine.stop()
        log.info("VoicePipeline stopped.")

    # ── Initialisation ────────────────────────────────────────

    def _init_and_start(self) -> None:
        """
        Run in love-init thread.
        Initialises Porcupine and Whisper, then launches WakeThread.
        Errors here are reported via on_error() and do NOT crash the UI.
        """
        try:
            self._init_porcupine()
            self._init_whisper()
            self._initialised = True
        except Exception as exc:
            log.error("Pipeline initialisation failed: %s", exc, exc_info=True)
            self._on_error(f"Voice engine failed to start: {exc}")
            return

        if not self._exit_event.is_set():
            self._launch_wake_thread()

    def _init_porcupine(self) -> None:
        cfg = self._cfg
        self._porcupine = PorcupineListener(
            access_key      = cfg.access_key,
            keyword_path    = cfg.keyword_path,
            builtin_keyword = cfg.builtin_keyword,
            sensitivity     = cfg.porcupine_sensitivity,
            device_index    = cfg.input_device,
        )
        self._porcupine.start()
        log.info("Porcupine engine ready.")

    def _init_whisper(self) -> None:
        cfg = self._cfg
        self._whisper = WhisperListener(
            model_size      = cfg.whisper_model,
            device          = cfg.whisper_device,
            compute_type    = cfg.whisper_compute,
            max_record_secs = cfg.max_record_secs,
            device_index    = cfg.input_device,
        )
        log.info("Whisper engine ready.")

    # ── Stage 1: Wake thread ──────────────────────────────────

    def _launch_wake_thread(self) -> None:
        self._wake_thread = threading.Thread(
            target = self._wake_loop,
            daemon = True,   # never blocks process exit
            name   = "love-wake",
        )
        # Verify daemon flag before start — guards against accidental changes
        assert self._wake_thread.daemon, "love-wake must be a daemon thread"
        self._wake_thread.start()
        log.info(
            "WakeThread (love-wake) started — daemon=%s pid-thread=%s",
            self._wake_thread.daemon, self._wake_thread.name,
        )

    def _wake_loop(self) -> None:
        """
        Permanent daemon loop running on love-wake thread.

        Each iteration processes one Porcupine frame (~32 ms).
        On keyword detection: notifies controller, then blocks
        until the command cycle completes.
        """
        log.debug("WakeThread: entering loop.")

        while not self._exit_event.is_set():
            try:
                detected = self._porcupine.process_frame()
            except RuntimeError as exc:
                # Porcupine was stopped (e.g. pipeline.stop() called)
                log.info("WakeThread: Porcupine stopped — exiting. (%s)", exc)
                break
            except Exception as exc:
                log.error("WakeThread frame error: %s", exc)
                self._on_error(f"Wake engine error: {exc}")
                continue

            if self._exit_event.is_set():
                break

            if detected:
                log.info("WakeThread: keyword detected — starting command cycle.")
                self._on_wake()            # -> controller._on_pipeline_wake()

                # Reset event before spawning command thread
                self._cmd_done.clear()

                cmd_thread = threading.Thread(
                    target = self._command_cycle,
                    daemon = True,   # exits if main thread exits
                    name   = "love-cmd",
                )
                cmd_thread.start()

                # Block WakeThread until command is captured.
                # This prevents TTS output from triggering another wake.
                self._cmd_done.wait()

                log.debug("WakeThread: command cycle complete — resuming wake detection.")

        log.info("WakeThread exited.")

    # ── Stage 2: Command cycle ────────────────────────────────

    def _command_cycle(self) -> None:
        """
        Run on love-cmd thread (one per wake event).

        Captures one audio clip, transcribes with Whisper,
        checks for stop words, then calls the appropriate callback.
        Signals _cmd_done when finished so WakeThread can resume.
        """
        try:
            if self._whisper is None:
                log.error("CommandThread: Whisper not initialised.")
                return

            log.debug("CommandThread: recording command audio...")
            text = self._whisper.record_and_transcribe()

            if self._exit_event.is_set():
                return

            if text is None:
                log.debug("CommandThread: no speech captured.")
                return

            log.info("CommandThread: transcribed '%s'", text)

            if self._is_stop_word(text):
                log.info("CommandThread: stop word detected.")
                self._on_stop()            # -> controller._on_pipeline_stop()
            else:
                self._on_command(text)     # -> controller._on_pipeline_command()

        except Exception as exc:
            log.error("CommandThread error: %s", exc, exc_info=True)
            self._on_error(f"Command recognition error: {exc}")
        finally:
            self._cmd_done.set()           # always unblock WakeThread

    # ── Word matching ─────────────────────────────────────────

    def _is_stop_word(self, text: str) -> bool:
        """Return True if *text* contains any configured stop word."""
        return any(w in text for w in self._stop_words)
