# ============================================================
#  LOVE v3 — Browser Commands
#  Handles every web-related action.
#  Uses webbrowser for URL navigation and pyautogui for
#  keyboard shortcuts that work across browsers.
# ============================================================

import time
import webbrowser
import pyautogui

from voice.speak import speak
from config.settings import URLS, BROWSER_TAB_DELAY


# ── Low-level helpers ────────────────────────────────────────

def new_tab() -> None:
    """Open a new browser tab with Ctrl+T."""
    pyautogui.hotkey("ctrl", "t")
    time.sleep(BROWSER_TAB_DELAY)


def close_tab() -> None:
    """Close the current browser tab with Ctrl+W."""
    pyautogui.hotkey("ctrl", "w")


def _open_url(url: str, label: str) -> None:
    """Open *url* in a new tab and announce it."""
    new_tab()
    webbrowser.open(url)
    speak(f"Opening {label}")


# ── Public command functions ─────────────────────────────────

def open_google() -> None:
    _open_url(URLS["google"], "Google")


def open_youtube() -> None:
    _open_url(URLS["youtube"], "YouTube")


def open_site(name: str) -> None:
    """
    Open any URL defined in settings.URLS by name.
    Falls back to a Google search if the name is unknown.
    """
    name = name.strip().lower()
    if name in URLS:
        _open_url(URLS[name], name.title())
    else:
        speak(f"I don't have {name} saved. Searching for it instead.")
        search_google(name)


def search_google(query: str) -> None:
    """Search Google for *query* in a new tab."""
    if not query:
        speak("What should I search for?")
        return
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    new_tab()
    webbrowser.open(url)
    speak(f"Searching for {query}")


def search_youtube(query: str) -> None:
    """Search YouTube for *query* in a new tab."""
    if not query:
        speak("What should I search on YouTube?")
        return
    url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    new_tab()
    webbrowser.open(url)
    speak(f"Searching YouTube for {query}")


def reload_page() -> None:
    """Reload the current browser tab with Ctrl+R."""
    pyautogui.hotkey("ctrl", "r")
    speak("Page reloaded")


def go_back() -> None:
    """Navigate back with Alt+Left."""
    pyautogui.hotkey("alt", "left")
    speak("Going back")


def go_forward() -> None:
    """Navigate forward with Alt+Right."""
    pyautogui.hotkey("alt", "right")
    speak("Going forward")


# ── Command registry ─────────────────────────────────────────
# Maps every phrase (or phrase pattern) to a callable.
# The processor imports this dict directly — no coupling to
# implementation details.

COMMANDS: dict[str, callable] = {
    "open google":          open_google,
    "open youtube":         open_youtube,
    "new tab":              new_tab,
    "close tab":            close_tab,
    "reload":               reload_page,
    "go back":              go_back,
    "go forward":           go_forward,
}

# Prefix commands that need the remainder of the utterance
# as an argument.  Format: prefix -> (function, arg_extractor)
PREFIX_COMMANDS: dict[str, callable] = {
    "search for":    search_google,
    "search":        search_google,
    "google":        search_google,
    "youtube search":search_youtube,
    "open site":     open_site,
    "open website":  open_site,
}
