# ================================================================
#  love_core.voice.speak
#  ----------------------------------------------------------------
#  Thread-safe text-to-speech powered by pyttsx3.
#
#  The engine is initialised once (singleton pattern) so that
#  multiple callers across an assistant's codebase share a single
#  engine instance and never conflict.
#
#  Usage
#  -----
#      from love_core.voice.speak import Speaker
#
#      tts = Speaker(rate=175, volume=1.0)
#      tts.speak("Hello, world.")
#
#  Or use the module-level convenience function:
#
#      from love_core.voice.speak import speak
#      speak("Hello, world.")
# ================================================================

from __future__ import annotations

import threading
from typing import Optional

import pyttsx3

from love_core.utils.logger import get_logger

log = get_logger(__name__)


class Speaker:
    """
    Wraps a pyttsx3 engine in a thread-safe singleton.

    Parameters
    ----------
    rate   : words per minute (default 175)
    volume : 0.0 – 1.0       (default 1.0)
    voice_index : which installed voice to use (default 0)
    """

    _instance: Optional["Speaker"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs) -> "Speaker":
        # Singleton — only one engine per process
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._ready = False
        return cls._instance

    def __init__(
        self,
        rate: int = 175,
        volume: float = 1.0,
        voice_index: int = 0,
    ) -> None:
        if self._ready:
            return   # already initialised — skip

        self._engine = pyttsx3.init()
        self._engine.setProperty("rate",   rate)
        self._engine.setProperty("volume", volume)

        voices = self._engine.getProperty("voices")
        if voices and 0 <= voice_index < len(voices):
            self._engine.setProperty("voice", voices[voice_index].id)

        self._speak_lock = threading.Lock()
        self._ready = True
        log.debug("Speaker initialised (rate=%d, volume=%.1f)", rate, volume)

    # ── Public API ────────────────────────────────────────────

    def speak(self, text: str) -> None:
        """
        Convert *text* to speech synchronously.

        Acquires a lock so concurrent callers do not overlap.
        Also echoes text to the logger at INFO level.
        """
        if not text:
            return
        log.info("speak › %s", text)
        with self._speak_lock:
            self._engine.say(text)
            self._engine.runAndWait()

    def set_rate(self, rate: int) -> None:
        """Change the speech rate (words per minute)."""
        self._engine.setProperty("rate", rate)

    def set_volume(self, volume: float) -> None:
        """Change the volume (0.0 – 1.0)."""
        self._engine.setProperty("volume", max(0.0, min(1.0, volume)))

    def available_voices(self) -> list[str]:
        """Return the IDs of all installed voices."""
        return [v.id for v in self._engine.getProperty("voices")]


# ── Module-level convenience ─────────────────────────────────
_default_speaker: Optional[Speaker] = None


def speak(text: str) -> None:
    """
    Speak *text* using a default Speaker instance.

    Calling this is equivalent to ``Speaker().speak(text)`` —
    the singleton is created on first use.
    """
    global _default_speaker
    if _default_speaker is None:
        _default_speaker = Speaker()
    _default_speaker.speak(text)
