# ================================================================
#  love_core.command_registry.registry
#  ----------------------------------------------------------------
#  The CommandRegistry is the heart of love_core's extensibility.
#
#  How it works
#  ────────────
#  Commands are stored in two internal tables:
#
#    _exact    : dict[phrase, CommandEntry]
#                "open youtube" → handler function
#
#    _prefix   : list[(prefix, CommandEntry)] sorted longest-first
#                "search for"  → handler(argument: str)
#
#  Matching (in order)
#  ───────────────────
#    1. Exact  — full utterance matches a registered phrase
#    2. Prefix — utterance starts with a registered prefix;
#                the remainder becomes the argument
#    3. No match → returns None (router decides fallback)
#
#  Adding commands
#  ───────────────
#  Use the @command decorator (see decorator.py) or call
#  registry.register() directly.  Both are equivalent.
#
#  Usage
#  -----
#      from love_core.command_registry.registry import CommandRegistry
#
#      registry = CommandRegistry()
#
#      registry.register("open youtube", open_youtube)
#      registry.register("search",       search_google, is_prefix=True)
#
#      fn, arg = registry.resolve("search python tutorial")
#      # fn  → search_google
#      # arg → "python tutorial"
# ================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from love_core.utils.logger import get_logger

log = get_logger(__name__)


# ── Data model ───────────────────────────────────────────────

@dataclass
class CommandEntry:
    """
    Metadata for a single registered command.

    Attributes
    ----------
    phrase      : the trigger phrase (exact or prefix)
    handler     : the callable to invoke
    is_prefix   : if True, remainder of utterance passed as arg
    description : human-readable description
    tags        : arbitrary labels for grouping / introspection
    """
    phrase      : str
    handler     : Callable
    is_prefix   : bool = False
    description : str  = ""
    tags        : list[str] = field(default_factory=list)

    def __repr__(self) -> str:
        kind = "prefix" if self.is_prefix else "exact"
        return f"<CommandEntry [{kind}] '{self.phrase}'>"


# ── Registry ─────────────────────────────────────────────────

class CommandRegistry:
    """
    Central store for all registered commands.

    One registry instance should be shared across an assistant
    implementation (pass it into the Router and command modules).

    Parameters
    ----------
    name : optional label for logging (e.g. "love_v4")
    """

    def __init__(self, name: str = "default") -> None:
        self.name = name
        self._exact  : dict[str, CommandEntry] = {}
        self._prefix : list[CommandEntry]      = []
        log.debug("CommandRegistry '%s' created", name)

    # ── Registration ─────────────────────────────────────────

    def register(
        self,
        phrase: str,
        handler: Callable,
        *,
        is_prefix: bool = False,
        description: str = "",
        tags: Optional[list[str]] = None,
        override: bool = False,
    ) -> CommandEntry:
        """
        Register a command handler.

        Parameters
        ----------
        phrase      : trigger phrase (exact match or prefix)
        handler     : callable — ``fn()`` for exact,
                      ``fn(arg: str)`` for prefix
        is_prefix   : when True, register as a prefix command
        description : human-readable description
        tags        : arbitrary grouping labels
        override    : silently replace an existing entry if True

        Returns
        -------
        CommandEntry
            The created entry (useful when called from a decorator).

        Raises
        ------
        ValueError
            If *phrase* is already registered and override=False.
        """
        phrase = phrase.strip().lower()
        entry  = CommandEntry(
            phrase      = phrase,
            handler     = handler,
            is_prefix   = is_prefix,
            description = description,
            tags        = tags or [],
        )

        if is_prefix:
            # Check for duplicates in prefix list
            existing = next((e for e in self._prefix if e.phrase == phrase), None)
            if existing and not override:
                raise ValueError(
                    f"Prefix command '{phrase}' already registered in "
                    f"registry '{self.name}'. Use override=True to replace."
                )
            if existing:
                self._prefix.remove(existing)
            self._prefix.append(entry)
            # Keep sorted longest-first for greedy matching
            self._prefix.sort(key=lambda e: len(e.phrase), reverse=True)
        else:
            if phrase in self._exact and not override:
                raise ValueError(
                    f"Exact command '{phrase}' already registered in "
                    f"registry '{self.name}'. Use override=True to replace."
                )
            self._exact[phrase] = entry

        log.debug("Registered %r", entry)
        return entry

    # ── Resolution ───────────────────────────────────────────

    def resolve(self, utterance: str) -> tuple[Optional[Callable], Optional[str]]:
        """
        Find the best-matching handler for *utterance*.

        Resolution order
        ----------------
        1. Exact match  → ``(handler, None)``
        2. Prefix match → ``(handler, argument_string)``
        3. No match     → ``(None, None)``

        Parameters
        ----------
        utterance : lower-cased input text from the voice layer

        Returns
        -------
        (callable, argument | None)
        """
        text = utterance.strip().lower()

        # 1. Exact
        if text in self._exact:
            entry = self._exact[text]
            log.debug("Resolved exact: '%s' → %s", text, entry.handler.__name__)
            return entry.handler, None

        # 2. Prefix (longest-first guarantees most specific wins)
        for entry in self._prefix:
            if text.startswith(entry.phrase):
                argument = text[len(entry.phrase):].strip()
                log.debug(
                    "Resolved prefix: '%s' → %s(arg='%s')",
                    entry.phrase, entry.handler.__name__, argument,
                )
                return entry.handler, argument

        log.debug("No match for: '%s'", text)
        return None, None

    # ── Introspection ─────────────────────────────────────────

    def all_commands(self) -> list[CommandEntry]:
        """Return every registered CommandEntry (exact + prefix)."""
        return list(self._exact.values()) + list(self._prefix)

    def commands_by_tag(self, tag: str) -> list[CommandEntry]:
        """Filter commands by a specific tag."""
        return [e for e in self.all_commands() if tag in e.tags]

    def phrases(self) -> list[str]:
        """Return a sorted list of every registered phrase."""
        return sorted(
            [e.phrase for e in self._exact.values()] +
            [e.phrase for e in self._prefix]
        )

    def __len__(self) -> int:
        return len(self._exact) + len(self._prefix)

    def __repr__(self) -> str:
        return (
            f"<CommandRegistry '{self.name}' "
            f"exact={len(self._exact)} prefix={len(self._prefix)}>"
        )


# ── Global default registry ──────────────────────────────────
# Modules that don't need a custom registry can import this.
default_registry = CommandRegistry(name="global")
