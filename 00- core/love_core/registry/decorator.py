# ================================================================
#  love_core.command_registry.decorator
#  ----------------------------------------------------------------
#  Provides the @command decorator so functions can self-register
#  without touching registry boilerplate.
#
#  Usage — exact command
#  ---------------------
#      from love_core.command_registry import command
#
#      @command("open youtube")
#      def open_youtube():
#          webbrowser.open("https://youtube.com")
#
#  Usage — prefix command (function receives the remainder)
#  --------------------------------------------------------
#      @command("search for", is_prefix=True, tags=["browser"])
#      def search_google(query: str):
#          webbrowser.open(f"https://google.com/search?q={query}")
#
#  Usage — custom registry (for modular assistant designs)
#  -------------------------------------------------------
#      from love_core.command_registry.registry import CommandRegistry
#      my_registry = CommandRegistry("love_v4")
#
#      @command("open youtube", registry=my_registry)
#      def open_youtube():
#          ...
#
#  The decorator does NOT change the function's signature or
#  behaviour — it still works as a plain Python function.
# ================================================================

from __future__ import annotations

from typing import Callable, Optional

from love_core.command_registry.registry import CommandRegistry, default_registry
from love_core.utils.logger import get_logger

log = get_logger(__name__)


def command(
    phrase: str,
    *,
    is_prefix: bool = False,
    description: str = "",
    tags: Optional[list[str]] = None,
    registry: Optional[CommandRegistry] = None,
    override: bool = False,
) -> Callable:
    """
    Decorator factory that registers a function as a command handler.

    Parameters
    ----------
    phrase      : trigger phrase (exact text or prefix)
    is_prefix   : if True, the remainder of the utterance is passed
                  as the first positional argument to the function
    description : human-readable summary (used for help / listing)
    tags        : arbitrary labels, e.g. ["browser", "navigation"]
    registry    : which CommandRegistry to use
                  (defaults to the global ``default_registry``)
    override    : replace an existing entry with the same phrase

    Returns
    -------
    The original function, unmodified.

    Examples
    --------
    >>> @command("open youtube", tags=["browser"])
    ... def open_youtube():
    ...     pass
    >>> "open youtube" in default_registry.phrases()
    True
    """
    target_registry = registry or default_registry

    def decorator(fn: Callable) -> Callable:
        # Use the function's docstring as description fallback
        desc = description or (fn.__doc__ or "").strip().split("\n")[0]

        target_registry.register(
            phrase,
            fn,
            is_prefix   = is_prefix,
            description = desc,
            tags        = tags or [],
            override    = override,
        )
        log.debug(
            "@command registered '%s' → %s.%s",
            phrase, fn.__module__, fn.__qualname__,
        )
        return fn   # return the function unchanged

    return decorator
