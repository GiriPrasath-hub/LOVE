# ================================================================
#  love_vH — environment/task_manager.py
#  Manages task difficulty progression and episode sequencing.
# ================================================================

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Literal

Difficulty = Literal["easy", "medium", "hard"]


@dataclass
class Task:
    difficulty    : Difficulty
    max_turns     : int
    done_on_first : bool   # episode ends after first correct response
    description   : str


# ── Task definitions ──────────────────────────────────────────

_TASKS: dict[Difficulty, Task] = {
    "easy": Task(
        difficulty    = "easy",
        max_turns     = 2,
        done_on_first = True,
        description   = "Simple direct request. Agent must respond accurately.",
    ),
    "medium": Task(
        difficulty    = "medium",
        max_turns     = 4,
        done_on_first = False,
        description   = "Ambiguous request. Agent must clarify and assist.",
    ),
    "hard": Task(
        difficulty    = "hard",
        max_turns     = 6,
        done_on_first = False,
        description   = "Emotional/complex user. Agent must de-escalate and resolve.",
    ),
}


class TaskManager:
    """
    Samples tasks according to configured difficulty weights and
    tracks episode progress.

    Parameters
    ----------
    difficulty_weights : mapping of difficulty → sampling probability
    rng_seed           : optional seed for reproducibility
    """

    def __init__(
        self,
        difficulty_weights: dict[str, float],
        rng_seed: int | None = None,
    ) -> None:
        self._weights  = difficulty_weights
        self._rng      = random.Random(rng_seed)
        self._episode  = 0
        self._turn     = 0
        self._task: Task | None = None

    # ── Public API ────────────────────────────────────────────

    def new_episode(self) -> Task:
        """Sample a fresh task for a new episode."""
        self._episode += 1
        self._turn     = 0
        difficulty     = self._sample_difficulty()
        self._task     = _TASKS[difficulty]
        return self._task

    def advance_turn(self) -> int:
        """Increment and return the current turn counter."""
        self._turn += 1
        return self._turn

    def is_done(self, reward: float, correct: bool) -> bool:
        """
        Determine whether the episode should end.

        Rules
        -----
        - easy: ends on first correct response OR max_turns reached
        - medium/hard: ends only on max_turns reached
        """
        if self._task is None:
            return True
        if self._turn >= self._task.max_turns:
            return True
        if self._task.done_on_first and correct:
            return True
        return False

    @property
    def current_task(self) -> Task | None:
        return self._task

    @property
    def current_difficulty(self) -> Difficulty:
        return self._task.difficulty if self._task else "easy"

    @property
    def turn(self) -> int:
        return self._turn

    @property
    def episode(self) -> int:
        return self._episode

    # ── Internal ──────────────────────────────────────────────

    def _sample_difficulty(self) -> Difficulty:
        difficulties = list(self._weights.keys())
        weights      = [self._weights[d] for d in difficulties]
        return self._rng.choices(difficulties, weights=weights, k=1)[0]  # type: ignore
