# ============================================================
#  LOVE v3 — Command Processor / Router
#
#  Architecture
#  ────────────
#  Each command module exposes two dicts:
#    COMMANDS        – exact phrase  → callable()
#    PREFIX_COMMANDS – prefix phrase → callable(arg: str)
#
#  Resolution order (first match wins, preventing duplicates):
#    1. Exact match in COMMANDS across all modules
#       (browser > app > system — most specific first)
#    2. Prefix match in PREFIX_COMMANDS (longest prefix wins)
#    3. Fallback: Google search for the full utterance
#
#  To add a new command module, just append it to MODULES.
# ============================================================

from __future__ import annotations

from voice.speak import speak
import commands.browser_commands as browser
import commands.app_commands     as app
import commands.system_commands  as system

# ── Module priority list ─────────────────────────────────────
# Order matters: earlier modules win on exact-match ties.
MODULES = [browser, app, system]


# ── Build merged lookup tables at import time ────────────────

def _build_exact_table() -> dict[str, callable]:
    """Merge COMMANDS dicts; earlier modules override later ones."""
    merged: dict[str, callable] = {}
    for mod in reversed(MODULES):          # reverse so earlier wins
        merged.update(mod.COMMANDS)
    return merged


def _build_prefix_table() -> list[tuple[str, callable]]:
    """
    Merge PREFIX_COMMANDS dicts into a list sorted by prefix
    length (longest first) so the most specific prefix wins.
    """
    merged: dict[str, callable] = {}
    for mod in reversed(MODULES):
        merged.update(mod.PREFIX_COMMANDS)
    return sorted(merged.items(), key=lambda kv: len(kv[0]), reverse=True)


_EXACT   = _build_exact_table()
_PREFIXES = _build_prefix_table()


# ── Public router ────────────────────────────────────────────

def process(utterance: str) -> None:
    """
    Route *utterance* to the correct command handler.

    This is the single entry-point called by LOVE Core.
    It guarantees each utterance triggers at most one action.
    """
    if not utterance:
        return

    text = utterance.lower().strip()

    # 1. Exact match ─────────────────────────────────────────
    if text in _EXACT:
        _EXACT[text]()
        return

    # 2. Prefix match ────────────────────────────────────────
    for prefix, fn in _PREFIXES:
        if text.startswith(prefix):
            argument = text[len(prefix):].strip()
            fn(argument)
            return

    # 3. Fallback ────────────────────────────────────────────
    speak(f"I'm not sure how to '{text}'. Searching online.")
    browser.search_google(text)


# ── Dev utility: list all registered commands ────────────────

def list_commands() -> list[str]:
    """Return a sorted list of every registered exact command phrase."""
    return sorted(_EXACT.keys())
