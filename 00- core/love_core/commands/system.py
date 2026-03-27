# ================================================================
#  love_core.commands.system
#  ----------------------------------------------------------------
#  OS-level commands: time, date, volume, screenshots, power.
#
#  Registration
#  ────────────
#      from love_core.commands.system import register_all
#      register_all()
# ================================================================

from __future__ import annotations

import datetime
import os
import time
from typing import Optional

import pyautogui

from love_core.command_registry.registry import CommandRegistry, default_registry
from love_core.utils.logger import get_logger

log = get_logger(__name__)


# ── Time & date ───────────────────────────────────────────────

def get_time() -> str:
    """Return the current time as a formatted string."""
    return datetime.datetime.now().strftime("%I:%M %p")


def get_date() -> str:
    """Return today's date as a formatted string."""
    return datetime.datetime.now().strftime("%A, %B %d %Y")


def tell_time() -> None:
    """Print the current time (assistants should override with speak)."""
    print(f"The time is {get_time()}")
    log.info("system: time → %s", get_time())


def tell_date() -> None:
    """Print today's date."""
    print(f"Today is {get_date()}")
    log.info("system: date → %s", get_date())


# ── Volume ────────────────────────────────────────────────────

def volume_up(steps: int = 5) -> None:
    """Raise system volume by *steps* key-presses."""
    for _ in range(steps):
        pyautogui.press("volumeup")
    log.debug("system: volume up ×%d", steps)


def volume_down(steps: int = 5) -> None:
    """Lower system volume by *steps* key-presses."""
    for _ in range(steps):
        pyautogui.press("volumedown")
    log.debug("system: volume down ×%d", steps)


def volume_mute() -> None:
    """Toggle mute."""
    pyautogui.press("volumemute")
    log.debug("system: mute toggled")


# ── Window management ─────────────────────────────────────────

def show_desktop() -> None:
    """Minimise all windows to reveal the desktop."""
    pyautogui.hotkey("win", "d")


def minimize_window() -> None:
    """Minimise the active window."""
    pyautogui.hotkey("win", "down")


def maximize_window() -> None:
    """Maximise the active window."""
    pyautogui.hotkey("win", "up")


# ── Screenshot ────────────────────────────────────────────────

def take_screenshot() -> str:
    """
    Capture the screen and save to ~/Pictures.

    Returns the full path of the saved file.
    """
    filename  = f"screenshot_{int(time.time())}.png"
    directory = os.path.join(os.path.expanduser("~"), "Pictures")
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    pyautogui.screenshot().save(path)
    log.info("system: screenshot saved → %s", path)
    return path


# ── Power management ──────────────────────────────────────────

def lock_computer() -> None:
    """Lock the workstation."""
    log.info("system: locking computer")
    os.system("rundll32.exe user32.dll,LockWorkStation")


def sleep_computer() -> None:
    """Put the computer to sleep."""
    log.info("system: sleep")
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")


def shutdown_computer() -> None:
    """Shutdown after a 10-second grace period."""
    log.warning("system: shutdown in 10s")
    time.sleep(10)
    os.system("shutdown /s /t 1")


def restart_computer() -> None:
    """Restart after a 10-second grace period."""
    log.warning("system: restart in 10s")
    time.sleep(10)
    os.system("shutdown /r /t 1")


# ── Registration helper ───────────────────────────────────────

def register_all(registry: Optional[CommandRegistry] = None) -> None:
    """Register all system commands into *registry*."""
    reg = registry or default_registry

    exact_map = {
        # time / date
        "what time is it":   tell_time,
        "what's the time":   tell_time,
        "time":              tell_time,
        "what's the date":   tell_date,
        "what day is it":    tell_date,
        "date":              tell_date,
        # volume
        "volume up":         volume_up,
        "volume down":       volume_down,
        "mute":              volume_mute,
        "unmute":            volume_mute,
        # windows
        "show desktop":      show_desktop,
        "minimize":          minimize_window,
        "maximize":          maximize_window,
        # screenshot
        "take a screenshot": take_screenshot,
        "screenshot":        take_screenshot,
        # power
        "lock":              lock_computer,
        "sleep":             sleep_computer,
        "shutdown":          shutdown_computer,
        "restart":           restart_computer,
    }

    for phrase, fn in exact_map.items():
        reg.register(phrase, fn, description=fn.__doc__ or "", tags=["system"])

    log.debug("system commands registered into '%s'", reg.name)
