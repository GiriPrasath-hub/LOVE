"""
love_core.command_registry
--------------------------
Command registration and lookup.

    from love_core.command_registry import command, CommandRegistry
    from love_core.command_registry.registry import default_registry
"""

from love_core.command_registry.registry  import CommandRegistry, CommandEntry, default_registry
from love_core.command_registry.decorator import command

__all__ = [
    "CommandRegistry",
    "CommandEntry",
    "default_registry",
    "command",
]
