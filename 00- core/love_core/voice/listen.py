# ================================================================
#  love_core.voice.listen
#  ----------------------------------------------------------------
#  Microphone input powered by SpeechRecognition.
#
#  The Listener class is stateful: it holds a shared Recognizer
#  and exposes a clean ``listen()`` method that returns either a
#  lower-cased string or None — no exceptions bubble up to callers.
#
#  Usage
#  -----
#      from love_core.voice.listen import Listener
#
#      mic = Listener(language="en-US", timeout=5)
#      text = mic.listen()    # returns str | None
#      if text:
#          print(text)
#
#  Module-level shortcut:
#
#      from love_core.voice.listen import listen
#      text = listen()
# ================================================================

from __future__ import annotations

from typing import Optional

import speech_recognition as sr

from love_core.utils.logger import get_logger

log = get_logger(__name__)


class Listener:
    """
    Stateful microphone listener.

    Parameters
    ----------
    language      : BCP-47 language tag (default "en-US")
    timeout       : seconds to wait for speech to start (default 5)
    phrase_limit  : max seconds for one phrase (default 10)
    energy_threshold : mic sensitivity; higher = less sensitive (default 300)
    pause_threshold  : seconds of silence that ends a phrase (default 0.8)
    """

    def __init__(
        self,
        language: str = "en-US",
        timeout: int = 5,
        phrase_limit: int = 10,
        energy_threshold: int = 300,
        pause_threshold: float = 0.8,
    ) -> None:
        self.language        = language
        self.timeout         = timeout
        self.phrase_limit    = phrase_limit

        self._recognizer = sr.Recognizer()
        self._recognizer.energy_threshold = energy_threshold
        self._recognizer.pause_threshold  = pause_threshold

        log.debug(
            "Listener initialised (lang=%s, timeout=%ds)",
            language, timeout,
        )

    # ── Public API ────────────────────────────────────────────

    def listen(self) -> Optional[str]:
        """
        Capture one utterance from the default microphone.

        Returns
        -------
        str
            Lower-cased, stripped recognised text.
        None
            On silence, unintelligible audio, or service error.
        """
        with sr.Microphone() as source:
            self._recognizer.adjust_for_ambient_noise(source, duration=0.3)
            log.debug("Listening…")
            try:
                audio = self._recognizer.listen(
                    source,
                    timeout=self.timeout,
                    phrase_time_limit=self.phrase_limit,
                )
                text = self._recognizer.recognize_google(
                    audio,
                    language=self.language,
                )
                result = text.lower().strip()
                log.info("heard › %s", result)
                return result

            except sr.WaitTimeoutError:
                log.debug("listen: timeout (silence)")
                return None
            except sr.UnknownValueError:
                log.debug("listen: audio not understood")
                return None
            except sr.RequestError as exc:
                log.error("listen: speech service error — %s", exc)
                return None

    def calibrate(self, duration: float = 1.0) -> None:
        """
        Adjust the energy threshold for ambient noise.

        Call this once at startup for best accuracy.
        """
        with sr.Microphone() as source:
            log.info("Calibrating for ambient noise (%.1fs)…", duration)
            self._recognizer.adjust_for_ambient_noise(source, duration=duration)
            log.info(
                "Calibration complete — energy threshold: %d",
                self._recognizer.energy_threshold,
            )


# ── Module-level convenience ─────────────────────────────────
_default_listener: Optional[Listener] = None


def listen(language: str = "en-US") -> Optional[str]:
    """
    Listen for one utterance using a default Listener instance.

    The default listener is created on first call.
    """
    global _default_listener
    if _default_listener is None:
        _default_listener = Listener(language=language)
    return _default_listener.listen()
