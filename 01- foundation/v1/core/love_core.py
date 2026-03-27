# ============================================================
#  LOVE v1 — Core Loop
#
#  Two states:
#    SLEEPING  — only listening for a wake word
#    AWAKE     — listening for one command, then back to sleep
# ============================================================

from voice.listen      import listen
from voice.speak       import speak
from brain.processor   import process
from config.settings   import WAKE_WORDS, STOP_WORD


def run() -> None:
    """Start LOVE v1 and block until the user says the stop word."""
    speak("LOVE version 1 is ready.")
    print("[LOVE] Sleeping — waiting for wake word...")

    awake = False

    while True:
        heard = listen()

        if heard is None:
            continue    # silence or error — keep looping

        # ── Sleeping state ───────────────────────────────────
        if not awake:
            if any(wake in heard for wake in WAKE_WORDS):
                awake = True
                speak("Hello. LOVE is listening.")
            # Ignore everything else while sleeping

        # ── Awake state ──────────────────────────────────────
        else:
            if STOP_WORD in heard:
                speak("Goodbye!")
                print("[LOVE] Stopped.")
                break

            # Execute the command, then go back to sleep
            process(heard)
            awake = False
            print("[LOVE] Sleeping — waiting for wake word...")
