# ================================================================
#  love_core.router.router
#  ----------------------------------------------------------------
#  The Router receives a raw utterance and dispatches it to the
#  correct handler via a CommandRegistry lookup.
#
#  It is the only component that knows about the three-step
#  dispatch flow:
#    1. Exact match
#    2. Prefix match
#    3. Fallback handler (configurable)
#
#  The Router is intentionally stateless with respect to
#  assistant logic (no wake words, no loops).  It processes
#  exactly one utterance per call.
#
#  Usage
#  -----
#      from love_core.router.router   import Router
#      from love_core.command_registry import CommandRegistry
#
#      registry = CommandRegistry("love_v4")
#      router   = Router(registry)
#
#      # Optional: provide a fallback for unrecognised input
#      router.set_fallback(lambda text: speak(f"Unknown: {text}"))
#
#      result = router.dispatch("open youtube")
#      # Returns a RouteResult describing what happened
# ================================================================

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Optional

from love_core.command_registry.registry import CommandRegistry, default_registry
from love_core.utils.logger import get_logger

log = get_logger(__name__)


# ── Result types ─────────────────────────────────────────────

class DispatchStatus(Enum):
    """Outcome of a single dispatch call."""
    MATCHED_EXACT    = auto()
    MATCHED_PREFIX   = auto()
    FALLBACK         = auto()
    NO_HANDLER       = auto()
    ERROR            = auto()


@dataclass
class RouteResult:
    """
    Return value from Router.dispatch().

    Attributes
    ----------
    utterance : the original input text
    status    : what kind of match occurred
    handler   : the callable that was invoked (or None)
    argument  : the argument passed to the handler (prefix commands)
    error     : exception object if status is ERROR
    """
    utterance : str
    status    : DispatchStatus
    handler   : Optional[Callable] = None
    argument  : Optional[str]      = None
    error     : Optional[Exception] = None

    @property
    def matched(self) -> bool:
        """True if any handler (including fallback) was called."""
        return self.status not in (DispatchStatus.NO_HANDLER, DispatchStatus.ERROR)


# ── Router ───────────────────────────────────────────────────

class Router:
    """
    Dispatches utterances to registered command handlers.

    Parameters
    ----------
    registry : CommandRegistry to use for lookups
               (defaults to the global default_registry)
    """

    def __init__(self, registry: Optional[CommandRegistry] = None) -> None:
        self._registry = registry or default_registry
        self._fallback : Optional[Callable[[str], None]] = None
        log.debug("Router attached to registry '%s'", self._registry.name)

    # ── Configuration ────────────────────────────────────────

    def set_fallback(self, handler: Callable[[str], None]) -> None:
        """
        Register a fallback callable for unrecognised utterances.

        The fallback receives the raw utterance string as its only
        argument.  Typical uses: Google search, "I don't understand"
        response, or logging for future training.
        """
        self._fallback = handler
        log.debug("Fallback handler set: %s", handler.__name__)

    # ── Dispatch ─────────────────────────────────────────────

    def dispatch(self, utterance: str) -> RouteResult:
        """
        Route *utterance* to the best matching handler and call it.

        Parameters
        ----------
        utterance : raw text (will be lower-cased internally)

        Returns
        -------
        RouteResult
            Always returned — even on error, so callers can decide
            how to respond without try/except boilerplate.
        """
        if not utterance or not utterance.strip():
            return RouteResult(utterance=utterance, status=DispatchStatus.NO_HANDLER)

        handler, argument = self._registry.resolve(utterance)

        # ── Matched ──────────────────────────────────────────
        if handler is not None:
            status = (
                DispatchStatus.MATCHED_PREFIX
                if argument is not None
                else DispatchStatus.MATCHED_EXACT
            )
            try:
                if argument is not None:
                    handler(argument)
                else:
                    handler()
                log.info(
                    "dispatch OK [%s] '%s' → %s",
                    status.name, utterance, handler.__name__,
                )
                return RouteResult(
                    utterance = utterance,
                    status    = status,
                    handler   = handler,
                    argument  = argument,
                )
            except Exception as exc:
                log.error(
                    "dispatch ERROR in '%s': %s", handler.__name__, exc,
                    exc_info=True,
                )
                return RouteResult(
                    utterance = utterance,
                    status    = DispatchStatus.ERROR,
                    handler   = handler,
                    argument  = argument,
                    error     = exc,
                )

        # ── No match — try fallback ───────────────────────────
        if self._fallback is not None:
            try:
                self._fallback(utterance)
                log.info("dispatch FALLBACK '%s'", utterance)
                return RouteResult(
                    utterance = utterance,
                    status    = DispatchStatus.FALLBACK,
                    handler   = self._fallback,
                )
            except Exception as exc:
                log.error("dispatch FALLBACK ERROR: %s", exc, exc_info=True)
                return RouteResult(
                    utterance = utterance,
                    status    = DispatchStatus.ERROR,
                    error     = exc,
                )

        log.warning("dispatch NO_HANDLER for: '%s'", utterance)
        return RouteResult(utterance=utterance, status=DispatchStatus.NO_HANDLER)
