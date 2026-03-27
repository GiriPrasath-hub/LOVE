# ============================================================
#  LOVE v3 — System Commands
#  Volume control, shutdown, sleep, clipboard, screenshots …
#  All OS-level actions that don't belong in browser or app.
# ============================================================

import os
import time
import datetime
import pyautogui

from voice.speak import speak


# ── Time & date ──────────────────────────────────────────────

def tell_time() -> None:
    now = datetime.datetime.now().strftime("%I:%M %p")
    speak(f"The time is {now}")


def tell_date() -> None:
    today = datetime.datetime.now().strftime("%A, %B %d %Y")
    speak(f"Today is {today}")


# ── Volume ───────────────────────────────────────────────────

def volume_up() -> None:
    for _ in range(5):
        pyautogui.press("volumeup")
    speak("Volume up")


def volume_down() -> None:
    for _ in range(5):
        pyautogui.press("volumedown")
    speak("Volume down")


def volume_mute() -> None:
    pyautogui.press("volumemute")
    speak("Muted")


# ── Screenshots ──────────────────────────────────────────────

def take_screenshot() -> None:
    filename = f"screenshot_{int(time.time())}.png"
    path     = os.path.join(os.path.expanduser("~"), "Pictures", filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    screenshot = pyautogui.screenshot()
    screenshot.save(path)
    speak(f"Screenshot saved to Pictures folder")


# ── Window management ────────────────────────────────────────

def minimize_window() -> None:
    pyautogui.hotkey("win", "down")
    speak("Window minimised")


def maximize_window() -> None:
    pyautogui.hotkey("win", "up")
    speak("Window maximised")


def show_desktop() -> None:
    pyautogui.hotkey("win", "d")
    speak("Showing desktop")


# ── Power ────────────────────────────────────────────────────

def sleep_computer() -> None:
    speak("Putting the computer to sleep")
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")


def lock_computer() -> None:
    speak("Locking the computer")
    os.system("rundll32.exe user32.dll,LockWorkStation")


def shutdown_computer() -> None:
    speak("Shutting down in 10 seconds. Say cancel to abort.")
    time.sleep(10)
    os.system("shutdown /s /t 1")


def restart_computer() -> None:
    speak("Restarting in 10 seconds.")
    time.sleep(10)
    os.system("shutdown /r /t 1")


# ── Clipboard ────────────────────────────────────────────────

def copy() -> None:
    pyautogui.hotkey("ctrl", "c")


def paste() -> None:
    pyautogui.hotkey("ctrl", "v")


# ── Command registry ─────────────────────────────────────────

COMMANDS: dict[str, callable] = {
    # time / date
    "what time is it":      tell_time,
    "what's the time":      tell_time,
    "tell me the time":     tell_time,
    "what's the date":      tell_date,
    "what day is it":       tell_date,
    # volume
    "volume up":            volume_up,
    "turn up volume":       volume_up,
    "volume down":          volume_down,
    "turn down volume":     volume_down,
    "mute":                 volume_mute,
    "unmute":               volume_mute,
    # screen
    "take a screenshot":    take_screenshot,
    "screenshot":           take_screenshot,
    # windows
    "minimize":             minimize_window,
    "maximize":             maximize_window,
    "show desktop":         show_desktop,
    # power
    "sleep":                sleep_computer,
    "lock":                 lock_computer,
    "shutdown":             shutdown_computer,
    "restart":              restart_computer,
}

PREFIX_COMMANDS: dict[str, callable] = {}
