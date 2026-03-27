from voice.listen import listen
from voice.speak import speak
from commands.system_commands import execute
from config.settings import WAKE_WORDS, STOP_WORD

def start():

    assistant_awake = False

    speak("LOVE is online. Say Hey Love to activate.")

    while True:

        command = listen()

        if command == "":
            continue

        # stop assistant
        if any(word in command for word in STOP_WORD):

            speak("Goodbye. Powered by LOVE.")
            break

        # wake assistant
        if any(word in command for word in WAKE_WORDS):

            assistant_awake = True
            speak("Hello. LOVE is listening.")
            continue

        # ignore commands while sleeping
        if not assistant_awake:
            print("LOVE is sleeping...")
            continue

        # execute command
        execute(command)
        assistant_awake = False