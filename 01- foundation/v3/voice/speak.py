# ============================================================
#  LOVE v3 — Voice Output
#  Wraps pyttsx3 in a thread-safe singleton so every module
#  can call speak() without creating multiple engine instances.
# ============================================================

import pyttsx3
import threading
from config.settings import TTS_RATE, TTS_VOLUME

# ── Singleton engine ─────────────────────────────────────────
_engine      = None
_engine_lock = threading.Lock()


def _get_engine() -> pyttsx3.Engine:
    """Initialise the TTS engine once and reuse it."""
    global _engine
    if _engine is None:
        _engine = pyttsx3.init()
        _engine.setProperty("rate",   TTS_RATE)
        _engine.setProperty("volume", TTS_VOLUME)
    return _engine


def speak(text: str) -> None:
    """
    Convert *text* to speech synchronously.

    Thread-safe: acquires a lock so concurrent callers
    don't corrupt the engine's internal state.
    """
    print(f"[LOVE] {text}")          # always echo to console
    with _engine_lock:
        engine = _get_engine()
        engine.say(text)
        engine.runAndWait()


def set_voice_by_index(index: int) -> None:
    """Switch to a different installed voice (0 = first, 1 = second …)."""
    engine = _get_engine()
    voices = engine.getProperty("voices")
    if 0 <= index < len(voices):
        engine.setProperty("voice", voices[index].id)
