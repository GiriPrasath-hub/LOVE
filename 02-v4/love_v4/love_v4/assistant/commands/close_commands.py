# ================================================================
#  love_v4.assistant.commands.close_commands
#  ----------------------------------------------------------------
#  Close running applications by process name using psutil.
#
#  Registration
#  ────────────
#      from assistant.commands.close_commands import register_all
#      register_all(registry=my_registry)
# ================================================================

from __future__ import annotations

from typing import Optional

try:
    import psutil
    _PSUTIL_AVAILABLE = True
except ImportError:
    _PSUTIL_AVAILABLE = False

from love_core.command_registry.registry import CommandRegistry
from love_core.utils.logger import get_logger

log = get_logger("love_v4.commands.close")

# Maps friendly app names → known process executable names
_PROCESS_MAP: dict[str, list[str]] = {
    "chrome":          ["chrome.exe", "googlechrome.exe"],
    "firefox":         ["firefox.exe"],
    "edge":            ["msedge.exe"],
    "notepad":         ["notepad.exe"],
    "calculator":      ["calculatorapp.exe", "calc.exe"],
    "vs code":         ["code.exe"],
    "vscode":          ["code.exe"],
    "whatsapp":        ["whatsapp.exe"],
    "spotify":         ["spotify.exe"],
    "discord":         ["discord.exe"],
    "slack":           ["slack.exe"],
    "teams":           ["teams.exe"],
    "zoom":            ["zoom.exe"],
    "vlc":             ["vlc.exe"],
    "paint":           ["mspaint.exe"],
    "word":            ["winword.exe"],
    "excel":           ["excel.exe"],
    "task manager":    ["taskmgr.exe"],
    "file explorer":   ["explorer.exe"],
}

# Speak callback — set by the controller after init
_speak_fn = print


def set_speak(fn) -> None:
    global _speak_fn
    _speak_fn = fn


def close_app(name: str) -> None:
    """
    Kill all processes matching *name* from the process map.

    Reports success or failure through the speak callback.
    """
    if not _PSUTIL_AVAILABLE:
        _speak_fn("psutil is not installed. Cannot close applications.")
        return

    name = name.strip().lower()
    exe_names = _PROCESS_MAP.get(name)

    if exe_names is None:
        # Try the raw name as an executable
        exe_names = [name if name.endswith(".exe") else f"{name}.exe"]

    killed = []
    for proc in psutil.process_iter(["name", "pid"]):
        try:
            proc_name = (proc.info["name"] or "").lower()
            if proc_name in exe_names:
                proc.terminate()
                killed.append(proc_name)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    if killed:
        _speak_fn(f"Closed {name}.")
        log.info("Closed: %s (processes: %s)", name, killed)
    else:
        _speak_fn(f"I couldn't find {name} running.")
        log.warning("close_app: no process found for '%s'", name)


def register_all(registry: Optional[CommandRegistry] = None) -> None:
    """Register close commands into *registry*."""
    from love_core.command_registry.registry import default_registry
    reg = registry or default_registry

    # Exact commands for common apps
    for app_name in _PROCESS_MAP:
        phrase = f"close {app_name}"
        fn = (lambda n: lambda: close_app(n))(app_name)
        fn.__doc__ = f"Close {app_name}."
        reg.register(phrase, fn, tags=["close", "apps"])

    # Generic prefix: "close <anything>"
    reg.register(
        "close",
        close_app,
        is_prefix=True,
        description="Close any running application by name.",
        tags=["close"],
    )

    log.debug("close commands registered into '%s'", reg.name)
