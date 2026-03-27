import webbrowser
import datetime
import os

from voice.speak import speak
from context.memory import is_duplicate


def execute(command):

    if is_duplicate(command):
        return

    # OPEN YOUTUBE
    elif "youtube" in command:

        speak("Opening YouTube")
        webbrowser.open("https://youtube.com")

    # OPEN GOOGLE
    elif "google" in command:

        speak("Opening Google")
        webbrowser.open("https://google.com")

    # OPEN VS CODE
    elif "vs code" in command or "vscode" in command or "visual studio code" in command:

        speak("Opening Visual Studio Code")
        os.startfile("C:\\Users\\anuvr\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe")

    # TIME
    elif "time" in command:

        now = datetime.datetime.now().strftime("%H:%M")
        speak(f"The time is {now}")

    # SEARCH GOOGLE
    elif "search" in command:

        query = command.replace("search", "")
        speak("Searching Google")
        webbrowser.open(f"https://www.google.com/search?q={query}")

    else:

        speak("Command not recognized")