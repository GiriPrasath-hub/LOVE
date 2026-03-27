# ============================================================
#  LOVE v3 — Voice Input (Optimized)
# ============================================================

import speech_recognition as sr
from config.settings import (
    RECOGNIZER_ENERGY_THRESHOLD,
    RECOGNIZER_PAUSE_THRESHOLD,
    RECOGNIZER_LANGUAGE,
)

# ── Shared recogniser ─────────────────────────────────────────
_recognizer = sr.Recognizer()
_recognizer.energy_threshold = RECOGNIZER_ENERGY_THRESHOLD
_recognizer.pause_threshold  = RECOGNIZER_PAUSE_THRESHOLD

# ── Shared microphone ─────────────────────────────────────────
_mic = sr.Microphone()

# ── Calibrate once at startup ─────────────────────────────────
with _mic as source:
    print("[LOVE] Calibrating microphone...")
    _recognizer.adjust_for_ambient_noise(source, duration=0.5)

print("[LOVE] Microphone ready.")


def listen(timeout: int = 5, phrase_limit: int = 10) -> str | None:
    """
    Listen for one utterance and return it as a lower-cased string.
    """

    with _mic as source:
        try:
            audio = _recognizer.listen(
                source,
                timeout=timeout,
                phrase_time_limit=phrase_limit,
            )

            text = _recognizer.recognize_google(
                audio,
                language=RECOGNIZER_LANGUAGE
            )

            return text.lower().strip()

        except sr.WaitTimeoutError:
            return None

        except sr.UnknownValueError:
            return None

        except sr.RequestError as exc:
            print(f"[listen] Speech service error: {exc}")
            return None