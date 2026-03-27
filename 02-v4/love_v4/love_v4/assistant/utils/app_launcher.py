# ================================================================
#  love_v4.assistant.utils.app_launcher
#  ----------------------------------------------------------------
#  Universal Windows application launcher.
#
#  Search order
#  ────────────
#  1. Start Menu shortcuts (.lnk) — ProgramData + user roaming
#  2. Executables in PATH
#  3. Program Files / Program Files (x86) — recursive .exe scan
#  4. Not found → caller receives None and can offer web fallback
#
#  Usage
#  -----
#      from assistant.utils.app_launcher import WindowsAppLauncher
#
#      launcher = WindowsAppLauncher()
#      result   = launcher.launch("spotify")
#      if not result:
#          # app not found — offer web fallback
# ================================================================

from __future__ import annotations

import os
import glob
import shutil
import subprocess
import threading
from typing import Optional

from love_core.utils.logger import get_logger

log = get_logger("love_v4.app_launcher")

# ── Alias table ───────────────────────────────────────────────
# Maps spoken name → canonical search term / executable hint
_ALIASES: dict[str, str] = {
    # Editors / IDEs
    "vs code":              "code",
    "vscode":               "code",
    "visual studio code":   "code",
    "visual studio":        "devenv",
    "pycharm":              "pycharm",
    "notepad plus":         "notepad++",
    "notepad++":            "notepad++",
    # Browsers
    "chrome":               "chrome",
    "google chrome":        "chrome",
    "firefox":              "firefox",
    "edge":                 "msedge",
    "microsoft edge":       "msedge",
    "brave":                "brave",
    "opera":                "opera",
    # Communication
    "whatsapp":             "whatsapp",
    "telegram":             "telegram",
    "discord":              "discord",
    "slack":                "slack",
    "teams":                "teams",
    "microsoft teams":      "teams",
    "zoom":                 "zoom",
    "skype":                "skype",
    "signal":               "signal",
    # Media
    "spotify":              "spotify",
    "vlc":                  "vlc",
    "media player":         "wmplayer",
    "netflix":              "netflix",
    "obs":                  "obs",
    "obs studio":           "obs",
    "audacity":             "audacity",
    # Productivity
    "word":                 "winword",
    "excel":                "excel",
    "powerpoint":           "powerpnt",
    "outlook":              "outlook",
    "onenote":              "onenote",
    "notepad":              "notepad",
    "paint":                "mspaint",
    "calculator":           "calc",
    "file explorer":        "explorer",
    "explorer":             "explorer",
    "task manager":         "taskmgr",
    # Creative
    "photoshop":            "photoshop",
    "illustrator":          "illustrator",
    "premiere":             "premiere",
    "after effects":        "afterfx",
    "blender":              "blender",
    "gimp":                 "gimp",
    # Gaming / Launchers
    "steam":                "steam",
    "epic games":           "epicgameslauncher",
    "epic":                 "epicgameslauncher",
    "xbox":                 "xboxapp",
    "minecraft":            "minecraft",
}

# Web fallbacks for apps that are commonly available as web apps
_WEB_FALLBACKS: dict[str, str] = {
    "spotify":   "https://open.spotify.com",
    "netflix":   "https://www.netflix.com",
    "discord":   "https://discord.com/app",
    "slack":     "https://app.slack.com",
    "teams":     "https://teams.microsoft.com",
    "outlook":   "https://outlook.live.com",
    "gmail":     "https://mail.google.com",
    "youtube":   "https://www.youtube.com",
    "notion":    "https://www.notion.so",
    "figma":     "https://www.figma.com",
    "canva":     "https://www.canva.com",
    "trello":    "https://trello.com",
}

# Start Menu search paths
_START_MENU_PATHS: list[str] = [
    r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
    os.path.join(
        os.environ.get("APPDATA", ""),
        r"Microsoft\Windows\Start Menu\Programs",
    ),
]

# Program Files directories
_PROGRAM_DIRS: list[str] = [
    r"C:\Program Files",
    r"C:\Program Files (x86)",
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs"),
]


class WindowsAppLauncher:
    """
    Finds and launches Windows applications using a multi-stage
    search strategy.

    The index is built lazily on first use and cached for the
    session (rebuild takes ~1-2 s on most machines).

    Parameters
    ----------
    speak_fn : callable(text) used to report results to the UI.
               Defaults to print; the controller replaces this.
    """

    def __init__(self, speak_fn=print) -> None:
        self._speak    = speak_fn
        self._index: Optional[dict[str, str]] = None   # name → path
        self._index_lock = threading.Lock()
        self._building   = False

        # Pre-build index in background so first query is fast
        threading.Thread(target=self._build_index, daemon=True).start()

    def set_speak(self, fn) -> None:
        self._speak = fn

    # ── Public API ────────────────────────────────────────────

    def launch(self, app_name: str) -> bool:
        """
        Attempt to launch *app_name*.

        Returns
        -------
        True   : application launched successfully
        False  : not found (caller should offer web fallback)
        """
        name      = app_name.strip().lower()
        canonical = _ALIASES.get(name, name)

        log.info("launch request: '%s' → canonical '%s'", name, canonical)

        # ── 1. PATH executables ───────────────────────────────
        path_exe = shutil.which(canonical) or shutil.which(name)
        if path_exe:
            return self._run(path_exe, name)

        # ── 2. Start Menu / index ─────────────────────────────
        index_path = self._lookup_index(canonical) or self._lookup_index(name)
        if index_path:
            return self._run(index_path, name)

        # ── 3. Program Files recursive scan ───────────────────
        found = self._scan_program_files(canonical) or self._scan_program_files(name)
        if found:
            return self._run(found, name)

        log.warning("App not found: '%s'", name)
        return False

    def web_fallback_url(self, app_name: str) -> Optional[str]:
        """Return a web fallback URL if one exists, else None."""
        name = app_name.strip().lower()
        return _WEB_FALLBACKS.get(name) or _WEB_FALLBACKS.get(_ALIASES.get(name, ""))

    def is_in_index(self, app_name: str) -> bool:
        """Quick check — returns True if we have any path for this app."""
        name = app_name.strip().lower()
        idx  = self._get_index()
        return (
            name in idx
            or _ALIASES.get(name, "") in idx
            or shutil.which(name) is not None
            or shutil.which(_ALIASES.get(name, name)) is not None
        )

    # ── Internal helpers ──────────────────────────────────────

    def _run(self, path: str, label: str) -> bool:
        try:
            subprocess.Popen([path], shell=False)
            log.info("Launched '%s' from '%s'", label, path)
            return True
        except Exception as exc:
            log.error("Failed to launch '%s': %s", path, exc)
            # Try shell=True as fallback for .lnk files etc.
            try:
                os.startfile(path)  # type: ignore[attr-defined]
                return True
            except Exception as exc2:
                log.error("os.startfile also failed: %s", exc2)
                return False

    def _lookup_index(self, name: str) -> Optional[str]:
        idx = self._get_index()
        # Exact key match
        if name in idx:
            return idx[name]
        # Partial match — find first key that contains the query
        for key, path in idx.items():
            if name in key:
                return path
        return None

    def _get_index(self) -> dict[str, str]:
        if self._index is None:
            with self._index_lock:
                if self._index is None:
                    self._build_index()
        return self._index  # type: ignore[return-value]

    def _build_index(self) -> None:
        """Scan Start Menu paths and build name → path dict."""
        with self._index_lock:
            if self._index is not None:
                return
            index: dict[str, str] = {}

            for base in _START_MENU_PATHS:
                if not os.path.isdir(base):
                    continue
                for lnk in glob.glob(os.path.join(base, "**", "*.lnk"), recursive=True):
                    stem = os.path.splitext(os.path.basename(lnk))[0].lower().strip()
                    index[stem] = lnk

            self._index = index
            log.debug("App index built: %d shortcuts indexed", len(index))

    def _scan_program_files(self, name: str) -> Optional[str]:
        """Search Program Files dirs for an exe whose stem matches *name*."""
        target = (name if name.endswith(".exe") else f"{name}.exe").lower()
        for base in _PROGRAM_DIRS:
            if not os.path.isdir(base):
                continue
            for root, _, files in os.walk(base):
                for f in files:
                    if f.lower() == target:
                        return os.path.join(root, f)
                # Don't recurse too deep — keep it fast
                depth = root[len(base):].count(os.sep)
                if depth >= 3:
                    break
        return None
