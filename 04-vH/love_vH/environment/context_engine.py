# ================================================================
#  love_vH - environment/context_engine.py
#  Maintains and retrieves conversational context for the agent.
# ================================================================

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Turn:
    """One exchange between user and agent."""
    turn_number  : int
    user_message : str
    agent_action : dict[str, Any]
    reward       : float
    mood         : str
    difficulty   : str


class ContextEngine:
    """
    Maintains a sliding window of recent conversation turns
    and exposes them as structured context for the agent's
    state representation.

    Parameters
    ----------
    window_size : how many past turns to retain
    """

    def __init__(self, window_size: int = 5) -> None:
        self._window_size = window_size
        self._history: deque[Turn] = deque(maxlen=window_size)
        self._episode_reward: float = 0.0

    def reset(self) -> None:
        """Clear history at the start of each episode."""
        self._history.clear()
        self._episode_reward = 0.0

    def record(self, turn: Turn) -> None:
        """Append a completed turn to the history."""
        self._history.append(turn)
        self._episode_reward += turn.reward

    def get_context(self) -> list[dict]:
        """
        Return history as a list of plain dicts for the state.
        """
        return [
            {
                "turn"         : t.turn_number,
                "user"         : t.user_message,
                "agent"        : t.agent_action.get("response", ""),
                "reward"       : t.reward,
                "mood"         : t.mood,
                "difficulty"   : t.difficulty,
            }
            for t in self._history
        ]

    def last_mood(self) -> str | None:
        """Return the mood from the most recent turn, or None."""
        return self._history[-1].mood if self._history else None

    def average_reward(self) -> float:
        """Running average reward over the current episode."""
        if not self._history:
            return 0.0
        return self._episode_reward / len(self._history)

    @property
    def episode_reward(self) -> float:
        return self._episode_reward
