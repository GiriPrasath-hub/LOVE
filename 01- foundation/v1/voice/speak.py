# ============================================================
#  LOVE v1 — Voice Output
#  Simple wrapper around pyttsx3.
# ============================================================

import pyttsx3
from config.settings import TTS_RATE, TTS_VOLUME

# Initialise engine once at module load
_engine = pyttsx3.init()
_engine.setProperty("rate",   TTS_RATE)
_engine.setProperty("volume", TTS_VOLUME)


def speak(text: str) -> None:
    """Say *text* aloud and also print it to the console."""
    print(f"[LOVE] {text}")
    _engine.say(text)
    _engine.runAndWait()
