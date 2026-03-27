from voice.speak import speak
from commands.system_commands import execute
from config.settings import WAKE_WORDS, STOP_WORD


def process(command):

    # STOP command
    if any(word in command for word in STOP_WORD):

        speak("Goodbye. Powered by LOVE.")
        return False


    # WAKE command
    if any(word in command for word in WAKE_WORDS):

        speak("Hello. LOVE is listening.")
        return "awake"


    return "idle"