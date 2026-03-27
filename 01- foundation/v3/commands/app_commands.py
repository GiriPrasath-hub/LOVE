# ============================================================
#  LOVE v3 — Application Commands
#  Opens desktop apps using os.startfile / subprocess.
#  APP_PATHS in config/settings.py defines the executables.
# ============================================================

import os
import subprocess

from voice.speak import speak
from config.settings import APP_PATHS


# ── Core launcher ────────────────────────────────────────────

def launch_app(name: str) -> None:
    """
    Launch a registered application by its friendly *name*.

    Looks up the path in APP_PATHS, expands environment
    variables (e.g. %USERNAME%), then launches it.
    """
    name = name.strip().lower()
    path = APP_PATHS.get(name)

    if path is None:
        speak(f"I don't know how to open {name}. You can add it in settings.")
        return

    expanded = os.path.expandvars(path)

    try:
        if os.path.isabs(expanded):
            subprocess.Popen([expanded])
        else:
            # Plain executable name — let the OS find it
            os.startfile(expanded)   # type: ignore[attr-defined]
        speak(f"Opening {name}")
    except FileNotFoundError:
        speak(f"I couldn't find {name}. It may not be installed.")
    except Exception as exc:
        speak(f"Failed to open {name}.")
        print(f"[app_commands] Error launching '{name}': {exc}")


# ── Convenience wrappers ─────────────────────────────────────

def open_vscode()         -> None: launch_app("vs code")
def open_notepad()        -> None: launch_app("notepad")
def open_calculator()     -> None: launch_app("calculator")
def open_chrome()         -> None: launch_app("chrome")
def open_firefox()        -> None: launch_app("firefox")
def open_file_explorer()  -> None: launch_app("file explorer")
def open_task_manager()   -> None: launch_app("task manager")
def open_paint()          -> None: launch_app("paint")
def open_word()           -> None: launch_app("word")
def open_excel()          -> None: launch_app("excel")


# ── Command registry ─────────────────────────────────────────

COMMANDS: dict[str, callable] = {
    "open vs code":         open_vscode,
    "open vscode":          open_vscode,
    "open notepad":         open_notepad,
    "open calculator":      open_calculator,
    "open chrome":          open_chrome,
    "open firefox":         open_firefox,
    "open file explorer":   open_file_explorer,
    "open explorer":        open_file_explorer,
    "open task manager":    open_task_manager,
    "open paint":           open_paint,
    "open word":            open_word,
    "open excel":           open_excel,
}

# Prefix commands: "open <app_name>" catches anything not in COMMANDS
PREFIX_COMMANDS: dict[str, callable] = {
    "open": launch_app,
}
