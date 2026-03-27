# ============================================================
#  LOVE v3 — Session Memory
#  Keeps a lightweight in-memory log of commands executed
#  during the current session.  No disk I/O — pure RAM.
#  Future versions can persist to SQLite or a JSON file.
# ============================================================

from __future__ import annotations
import datetime
from dataclasses import dataclass, field
from collections import deque

MAX_HISTORY = 100      # how many entries to keep in memory


@dataclass
class MemoryEntry:
    timestamp: datetime.datetime
    utterance: str
    resolved:  bool          # True = matched a command, False = fallback


class SessionMemory:
    """Stores the command history for the current LOVE session."""

    def __init__(self, max_size: int = MAX_HISTORY):
        self._history: deque[MemoryEntry] = deque(maxlen=max_size)

    def record(self, utterance: str, resolved: bool = True) -> None:
        self._history.append(
            MemoryEntry(
                timestamp=datetime.datetime.now(),
                utterance=utterance,
                resolved=resolved,
            )
        )

    @property
    def last(self) -> MemoryEntry | None:
        return self._history[-1] if self._history else None

    def recent(self, n: int = 5) -> list[MemoryEntry]:
        return list(self._history)[-n:]

    def clear(self) -> None:
        self._history.clear()

    def __len__(self) -> int:
        return len(self._history)


# ── Module-level singleton ───────────────────────────────────
# Import and use this directly: `from context.memory import memory`
memory = SessionMemory()
