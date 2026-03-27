# ================================================================
#  love_v4.assistant.commands.extended_browser
#  ----------------------------------------------------------------
#  Browser commands that produce spoken feedback in the UI.
#  These override / extend love_core's silent browser module.
# ================================================================

from __future__ import annotations

import time
import webbrowser
from typing import Optional

import pyautogui

from love_core.command_registry.registry import CommandRegistry
from love_core.utils.logger import get_logger

log = get_logger("love_v4.commands.browser_ext")

_speak_fn = print   # replaced by controller.respond at runtime


def set_speak(fn) -> None:
    global _speak_fn
    _speak_fn = fn


# ── URL table ────────────────────────────────────────────────
_URLS: dict[str, str] = {
    "youtube":    "https://www.youtube.com",
    "google":     "https://www.google.com",
    "github":     "https://www.github.com",
    "gmail":      "https://mail.google.com",
    "maps":       "https://maps.google.com",
    "reddit":     "https://www.reddit.com",
    "wikipedia":  "https://www.wikipedia.org",
    "twitter":    "https://www.twitter.com",
    "linkedin":   "https://www.linkedin.com",
    "spotify":    "https://open.spotify.com",
    "netflix":    "https://www.netflix.com",
}


def open_youtube() -> None:
    """Open YouTube in the default browser."""
    _speak_fn("Opening YouTube.")
    webbrowser.open(_URLS["youtube"])


def open_google() -> None:
    """Open Google in the default browser."""
    _speak_fn("Opening Google.")
    webbrowser.open(_URLS["google"])


def open_site(name: str) -> None:
    """Open a named website, or search if not in the table."""
    name = name.strip().lower()
    if name in _URLS:
        _speak_fn(f"Opening {name.title()}.")
        webbrowser.open(_URLS[name])
    else:
        _speak_fn(f"I don't have {name} saved. Searching for it.")
        search_google(name)


def search_google(query: str) -> None:
    """Search Google for the given query."""
    if not query:
        _speak_fn("What should I search for?")
        return
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    pyautogui.hotkey("ctrl", "t")
    time.sleep(0.3)
    webbrowser.open(url)
    _speak_fn(f"Searching for {query}.")


def search_youtube(query: str) -> None:
    """Search YouTube for the given query."""
    if not query:
        return
    url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    pyautogui.hotkey("ctrl", "t")
    time.sleep(0.3)
    webbrowser.open(url)
    _speak_fn(f"Searching YouTube for {query}.")


def new_tab() -> None:
    """Open a new browser tab."""
    pyautogui.hotkey("ctrl", "t")
    _speak_fn("New tab opened.")


def close_tab() -> None:
    """Close the current browser tab."""
    pyautogui.hotkey("ctrl", "w")
    _speak_fn("Tab closed.")


def go_back() -> None:
    pyautogui.hotkey("alt", "left")
    _speak_fn("Going back.")


def go_forward() -> None:
    pyautogui.hotkey("alt", "right")
    _speak_fn("Going forward.")


def reload_page() -> None:
    pyautogui.hotkey("ctrl", "r")
    _speak_fn("Page reloaded.")


def register_all(registry: Optional[CommandRegistry] = None) -> None:
    """Register all extended browser commands, overriding love_core defaults."""
    from love_core.command_registry.registry import default_registry
    reg = registry or default_registry

    exact = {
        "open youtube":  open_youtube,
        "open google":   open_google,
        "new tab":       new_tab,
        "close tab":     close_tab,
        "go back":       go_back,
        "go forward":    go_forward,
        "reload":        reload_page,
        "reload page":   reload_page,
    }
    for phrase, fn in exact.items():
        reg.register(phrase, fn, tags=["browser"], override=True)

    prefix = {
        "open site":      open_site,
        "open website":   open_site,
        "search for":     search_google,
        "search":         search_google,
        "google":         search_google,
        "youtube search": search_youtube,
    }
    for phrase, fn in prefix.items():
        reg.register(phrase, fn, is_prefix=True, tags=["browser"], override=True)

    log.debug("extended browser commands registered into '%s'", reg.name)
