# ============================================================
#  LOVE v1 — Command Processor
#  Maps what the user said to the right command function.
#  Kept intentionally simple: plain if/elif checks.
# ============================================================

from voice.speak       import speak
from commands.system_commands import (
    open_youtube,
    open_google,
    open_vscode,
    tell_time,
)


def process(command: str) -> None:
    """
    Receive a recognised *command* string and run the
    matching function.  Falls back to a polite message
    if nothing matches.
    """
    if "open youtube" in command:
        open_youtube()

    elif "open google" in command:
        open_google()

    elif "open vscode" in command or "open vs code" in command:
        open_vscode()

    elif "time" in command:
        tell_time()

    else:
        speak("Sorry, I didn't understand that command.")
