# ================================================================
#  love_core.memory.session
#  ----------------------------------------------------------------
#  Lightweight in-process session memory.
#
#  Tracks every command dispatched during a single assistant run.
#  Designed to be extended in future versions with persistence
#  (SQLite, JSON), NLP context, or user profiles.
#
#  Usage
#  -----
#      from love_core.memory.session import SessionMemory
#
#      mem = SessionMemory(max_entries=200)
#      mem.record("open youtube", resolved=True)
#
#      last    = mem.last
#      recent  = mem.recent(5)
#      history = mem.all()
#      mem.clear()
# ================================================================

from __future__ import annotations

import datetime
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from love_core.utils.logger import get_logger

log = get_logger(__name__)

_DEFAULT_MAX = 100


# ── Data model ───────────────────────────────────────────────

@dataclass
class MemoryEntry:
    """
    A single recorded utterance.

    Attributes
    ----------
    utterance  : the raw text that was spoken
    timestamp  : when it was recorded
    resolved   : True if a handler was found, False for fallback / miss
    metadata   : arbitrary key/value pairs for extensions
    """
    utterance  : str
    timestamp  : datetime.datetime = field(
        default_factory=datetime.datetime.now
    )
    resolved   : bool = True
    metadata   : dict = field(default_factory=dict)

    def age_seconds(self) -> float:
        """Seconds since this entry was recorded."""
        return (datetime.datetime.now() - self.timestamp).total_seconds()

    def __repr__(self) -> str:
        ts = self.timestamp.strftime("%H:%M:%S")
        ok = "✓" if self.resolved else "✗"
        return f"<MemoryEntry [{ok}] {ts} '{self.utterance}'>"


# ── Session memory ────────────────────────────────────────────

class SessionMemory:
    """
    Rolling in-memory log of commands processed in this session.

    Parameters
    ----------
    max_entries : maximum number of entries to retain (FIFO eviction)
    """

    def __init__(self, max_entries: int = _DEFAULT_MAX) -> None:
        self._max     = max_entries
        self._entries : deque[MemoryEntry] = deque(maxlen=max_entries)
        self._session_start = datetime.datetime.now()
        log.debug("SessionMemory initialised (max=%d)", max_entries)

    # ── Write ────────────────────────────────────────────────

    def record(
        self,
        utterance: str,
        resolved: bool = True,
        **metadata,
    ) -> MemoryEntry:
        """
        Add an entry to the session log.

        Parameters
        ----------
        utterance : the spoken command text
        resolved  : whether a handler was matched
        **metadata: any extra context to store with the entry

        Returns
        -------
        MemoryEntry — the newly created entry
        """
        entry = MemoryEntry(
            utterance = utterance,
            resolved  = resolved,
            metadata  = metadata,
        )
        self._entries.append(entry)
        log.debug("memory: recorded %r", entry)
        return entry

    # ── Read ─────────────────────────────────────────────────

    @property
    def last(self) -> Optional[MemoryEntry]:
        """The most recent entry, or None if empty."""
        return self._entries[-1] if self._entries else None

    def recent(self, n: int = 5) -> list[MemoryEntry]:
        """Return the *n* most recent entries (newest last)."""
        return list(self._entries)[-n:]

    def all(self) -> list[MemoryEntry]:
        """Return all entries in chronological order."""
        return list(self._entries)

    def unresolved(self) -> list[MemoryEntry]:
        """Return entries where no handler was found."""
        return [e for e in self._entries if not e.resolved]

    def since(self, seconds: float) -> list[MemoryEntry]:
        """Return entries recorded within the last *seconds*."""
        return [e for e in self._entries if e.age_seconds() <= seconds]

    # ── Session info ─────────────────────────────────────────

    @property
    def session_duration(self) -> datetime.timedelta:
        """How long this session has been running."""
        return datetime.datetime.now() - self._session_start

    def summary(self) -> dict:
        """Return a dict of basic session statistics."""
        total    = len(self._entries)
        resolved = sum(1 for e in self._entries if e.resolved)
        return {
            "total"          : total,
            "resolved"       : resolved,
            "unresolved"     : total - resolved,
            "session_start"  : self._session_start.isoformat(),
            "session_seconds": self.session_duration.total_seconds(),
        }

    # ── Maintenance ──────────────────────────────────────────

    def clear(self) -> None:
        """Erase all entries."""
        self._entries.clear()
        log.debug("memory: cleared")

    # ── Dunder ───────────────────────────────────────────────

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self):
        return iter(self._entries)

    def __repr__(self) -> str:
        return (
            f"<SessionMemory entries={len(self)} "
            f"uptime={int(self.session_duration.total_seconds())}s>"
        )
