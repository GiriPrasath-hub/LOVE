# ================================================================
#  love_core.commands.browser
#  ----------------------------------------------------------------
#  Ready-to-use browser commands.
#
#  These are example implementations that assistant projects can
#  import and register, or use as a reference for their own.
#
#  Registration
#  ────────────
#  Two ways to load these commands into a registry:
#
#  A) Auto-register into the global default_registry:
#
#      from love_core.commands import browser
#      browser.register_all()
#
#  B) Register into a custom registry:
#
#      from love_core.commands.browser import register_all
#      from love_core.command_registry import CommandRegistry
#
#      my_reg = CommandRegistry("love_v4")
#      register_all(registry=my_reg)
# ================================================================

from __future__ import annotations

import time
import webbrowser
from typing import Optional

import pyautogui

from love_core.command_registry.registry import CommandRegistry, default_registry
from love_core.utils.logger import get_logger

log = get_logger(__name__)

# ── URLs ────────────────────────────────────────────────────
_URLS: dict[str, str] = {
    "google":    "https://www.google.com",
    "youtube":   "https://www.youtube.com",
    "github":    "https://www.github.com",
    "gmail":     "https://mail.google.com",
    "maps":      "https://maps.google.com",
    "reddit":    "https://www.reddit.com",
    "wikipedia": "https://www.wikipedia.org",
}


# ── Helpers ──────────────────────────────────────────────────

def _open(url: str) -> None:
    webbrowser.open(url)
    log.info("browser: opened %s", url)


# ── Command functions ────────────────────────────────────────

def open_google() -> None:
    """Open Google in the default browser."""
    _open(_URLS["google"])


def open_youtube() -> None:
    """Open YouTube in the default browser."""
    _open(_URLS["youtube"])


def open_site(name: str) -> None:
    """
    Open a named site from the internal URL table.
    Falls back to a Google search if the name is not registered.
    """
    name = name.strip().lower()
    if name in _URLS:
        _open(_URLS[name])
    else:
        log.warning("browser: unknown site '%s' — falling back to search", name)
        search_google(name)


def search_google(query: str) -> None:
    """Search Google for *query* in a new tab."""
    if not query:
        log.warning("search_google called with empty query")
        return
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    new_tab()
    _open(url)


def search_youtube(query: str) -> None:
    """Search YouTube for *query* in a new tab."""
    if not query:
        return
    url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    new_tab()
    _open(url)


def new_tab() -> None:
    """Open a new browser tab (Ctrl+T)."""
    pyautogui.hotkey("ctrl", "t")
    time.sleep(0.3)
    log.debug("browser: new tab")


def close_tab() -> None:
    """Close the current browser tab (Ctrl+W)."""
    pyautogui.hotkey("ctrl", "w")
    log.debug("browser: close tab")


def go_back() -> None:
    """Navigate back (Alt+Left)."""
    pyautogui.hotkey("alt", "left")


def go_forward() -> None:
    """Navigate forward (Alt+Right)."""
    pyautogui.hotkey("alt", "right")


def reload_page() -> None:
    """Reload the current page (Ctrl+R)."""
    pyautogui.hotkey("ctrl", "r")


# ── Registration helper ──────────────────────────────────────

def register_all(registry: Optional[CommandRegistry] = None) -> None:
    """
    Register every browser command into *registry*.

    If *registry* is None the global default_registry is used.
    """
    reg = registry or default_registry

    # Exact commands
    for phrase, fn in {
        "open google":   open_google,
        "open youtube":  open_youtube,
        "new tab":       new_tab,
        "close tab":     close_tab,
        "go back":       go_back,
        "go forward":    go_forward,
        "reload":        reload_page,
        "reload page":   reload_page,
    }.items():
        reg.register(phrase, fn, description=fn.__doc__ or "", tags=["browser"])

    # Prefix commands
    for phrase, fn in {
        "search for":     search_google,
        "search":         search_google,
        "google":         search_google,
        "youtube search": search_youtube,
        "open site":      open_site,
    }.items():
        reg.register(
            phrase, fn,
            is_prefix=True,
            description=fn.__doc__ or "",
            tags=["browser"],
        )

    log.debug("browser commands registered into '%s'", reg.name)
