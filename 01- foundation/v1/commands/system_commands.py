# ============================================================
#  LOVE v1 — System Commands
#  Each function does exactly one thing and speaks its result.
# ============================================================

import os
import webbrowser
import datetime

from voice.speak import speak


def open_youtube() -> None:
    speak("Opening YouTube.")
    webbrowser.open("https://www.youtube.com")


def open_google() -> None:
    speak("Opening Google.")
    webbrowser.open("https://www.google.com")


def open_vscode() -> None:
    speak("Opening VS Code.")
    # Works on Windows; adjust the path for macOS / Linux if needed
    os.system("code")


def tell_time() -> None:
    now  = datetime.datetime.now()
    time_str = now.strftime("%I:%M %p")
    speak(f"The current time is {time_str}.")
