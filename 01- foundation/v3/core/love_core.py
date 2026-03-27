# ============================================================
#  LOVE v3 — Core Event Loop
#
#  State machine
#  ─────────────
#    SLEEPING  ──(wake word)──►  AWAKE
#    AWAKE     ──(command)───►  SLEEPING
#    AWAKE     ──(stop word)──►  EXIT
#    AWAKE     ──(timeout)───►  SLEEPING
#
#  This module is the only place that knows about the wake /
#  stop words.  All command logic lives in brain/processor.py.
# ============================================================

from __future__ import annotations

from voice.listen  import listen
from voice.speak   import speak
from brain.processor import process
from context.memory  import memory
from config.settings import WAKE_WORD, STOP_WORD


# ── State constants ──────────────────────────────────────────
_SLEEPING = "sleeping"
_AWAKE    = "awake"


class LOVECore:
    """
    Main controller for LOVE v3.

    Call ``run()`` to start the blocking event loop.
    """

    def __init__(self) -> None:
        self._state     = _SLEEPING
        self._running   = False

    # ── Public ───────────────────────────────────────────────

    def run(self) -> None:
        """Start LOVE.  Blocks until the user says the stop word."""
        self._running = True
        speak("LOVE v3 is online. Say hey love to wake me up.")
        print("[LOVE] Entering main loop — state: SLEEPING")

        while self._running:
            utterance = listen()

            if utterance is None:
                continue    # silence or recognition error — keep looping

            if self._state == _SLEEPING:
                self._handle_sleeping(utterance)
            else:
                self._handle_awake(utterance)

    def stop(self) -> None:
        """Gracefully stop the event loop from another thread."""
        self._running = False

    # ── Private ──────────────────────────────────────────────

    def _handle_sleeping(self, utterance: str) -> None:
        """Only react to the wake word while sleeping."""
        if WAKE_WORD in utterance:
            self._state = _AWAKE
            speak("Hey! I'm listening.")
            print("[LOVE] State → AWAKE")

    def _handle_awake(self, utterance: str) -> None:
        """
        Execute one command then go back to sleep.

        Prevents duplicate execution: process() is called exactly
        once per wake cycle, regardless of what was said.
        """
        # Stop word → shut down
        if STOP_WORD in utterance:
            speak("Goodbye! Have a great day.")
            print("[LOVE] Stop word received — shutting down.")
            memory.record(utterance, resolved=True)
            self._running = False
            return

        # Wake word repeated → re-acknowledge, stay awake
        if WAKE_WORD in utterance:
            speak("Still here! Go ahead.")
            return

        # Route to command processor ── exactly once
        print(f"[LOVE] Command received: '{utterance}'")
        process(utterance)
        memory.record(utterance, resolved=True)

        # Return to sleep after one command
        self._state = _SLEEPING
        print("[LOVE] State → SLEEPING")
