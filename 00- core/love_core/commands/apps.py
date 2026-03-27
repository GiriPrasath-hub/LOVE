# ================================================================
#  love_core.commands.apps
#  ----------------------------------------------------------------
#  Desktop application launcher commands.
#
#  APP_PATHS maps friendly names → executable paths/commands.
#  Values support %ENVVAR% expansion (Windows) and plain
#  executable names that are resolved via PATH.
#
#  Registration
#  ────────────
#      from love_core.commands.apps import register_all
#      register_all()                          # global registry
#      register_all(registry=my_reg)           # custom registry
# ================================================================

from __future__ import annotations

import os
import subprocess
from typing import Optional

from love_core.command_registry.registry import CommandRegistry, default_registry
from love_core.utils.logger import get_logger

log = get_logger(__name__)

# ── Application table ─────────────────────────────────────────
APP_PATHS: dict[str, str] = {
    # Windows built-ins (work via PATH)
    "notepad":        "notepad.exe",
    "calculator":     "calc.exe",
    "paint":          "mspaint.exe",
    "file explorer":  "explorer.exe",
    "task manager":   "taskmgr.exe",
    # VS Code — expand %USERNAME% at runtime
    "vs code": (
        r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"
    ),
    "vscode": (
        r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"
    ),
    # Browsers
    "chrome":   r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "firefox":  r"C:\Program Files\Mozilla Firefox\firefox.exe",
    # Office
    "word":  r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel": r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
}


# ── Core launcher ─────────────────────────────────────────────

def launch(app_name: str) -> None:
    """
    Launch an application by its friendly name.

    Looks up *app_name* in APP_PATHS, expands environment variables,
    then launches it via subprocess.  Falls back to os.startfile for
    plain executable names.
    """
    key  = app_name.strip().lower()
    path = APP_PATHS.get(key)

    if path is None:
        log.warning("apps: unknown app '%s'", key)
        return

    expanded = os.path.expandvars(path)

    try:
        if os.path.isabs(expanded):
            subprocess.Popen([expanded])
        else:
            os.startfile(expanded)  # type: ignore[attr-defined]
        log.info("apps: launched '%s' (%s)", key, expanded)
    except FileNotFoundError:
        log.error("apps: '%s' not found at '%s'", key, expanded)
    except Exception as exc:
        log.error("apps: failed to launch '%s' — %s", key, exc)


# ── Named wrappers (used as exact-command handlers) ───────────

def open_vscode()        -> None: launch("vs code")
def open_notepad()       -> None: launch("notepad")
def open_calculator()    -> None: launch("calculator")
def open_chrome()        -> None: launch("chrome")
def open_firefox()       -> None: launch("firefox")
def open_file_explorer() -> None: launch("file explorer")
def open_task_manager()  -> None: launch("task manager")
def open_paint()         -> None: launch("paint")
def open_word()          -> None: launch("word")
def open_excel()         -> None: launch("excel")


# ── Registration helper ───────────────────────────────────────

def register_all(registry: Optional[CommandRegistry] = None) -> None:
    """Register all application commands into *registry*."""
    reg = registry or default_registry

    exact_map: dict[str, object] = {
        "open vs code":       open_vscode,
        "open vscode":        open_vscode,
        "open notepad":       open_notepad,
        "open calculator":    open_calculator,
        "open chrome":        open_chrome,
        "open firefox":       open_firefox,
        "open file explorer": open_file_explorer,
        "open explorer":      open_file_explorer,
        "open task manager":  open_task_manager,
        "open paint":         open_paint,
        "open word":          open_word,
        "open excel":         open_excel,
    }

    for phrase, fn in exact_map.items():
        reg.register(phrase, fn, description=fn.__doc__ or "", tags=["apps"])

    # Generic prefix: "open <anything>" resolves unknown apps via launch()
    reg.register(
        "open", launch,
        is_prefix=True,
        description="Open any registered application by name.",
        tags=["apps"],
    )

    log.debug("app commands registered into '%s'", reg.name)
