# ============================================================
#  LOVE v1 — Voice Input
#  Listens to the microphone and returns a lowercase string.
# ============================================================

import speech_recognition as sr
from config.settings import LANGUAGE

_recognizer = sr.Recognizer()


def listen() -> str | None:
    """
    Record one utterance from the microphone.

    Returns the recognised text in lowercase,
    or None if nothing could be understood.
    """
    with sr.Microphone() as source:
        _recognizer.adjust_for_ambient_noise(source, duration=0.3)
        print("[LOVE] Listening...")
        try:
            audio = _recognizer.listen(source, timeout=5, phrase_time_limit=8)
            text  = _recognizer.recognize_google(audio, language=LANGUAGE)
            print(f"[LOVE] Heard: {text}")
            return text.lower().strip()
        except sr.WaitTimeoutError:
            return None   # silence — normal, keep looping
        except sr.UnknownValueError:
            return None   # couldn't understand
        except sr.RequestError as e:
            print(f"[LOVE] Speech service error: {e}")
            return None
