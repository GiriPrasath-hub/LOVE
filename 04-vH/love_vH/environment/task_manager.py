from __future__ import annotations
import random
from dataclasses import dataclass
from typing import Literal

Difficulty = Literal["easy", "medium", "hard"]


@dataclass
class Task:
    difficulty: Difficulty
    max_turns: int
    done_on_first: bool
    description: str


_TASKS = {
    "easy": Task("easy", 2, True, "Simple request"),
    "medium": Task("medium", 4, False, "Ambiguous request"),
    "hard": Task("hard", 6, False, "Emotional / complex interaction"),
}


class TaskManager:
    def __init__(self, difficulty_weights: dict[str, float], seed: int = 42):
        self._weights = difficulty_weights
        self._rng = random.Random(seed)
        self._episode = 0
        self._turn = 0
        self._task: Task | None = None

    def new_episode(self) -> Task:
        self._episode += 1
        self._turn = 0
        difficulty = self._sample_difficulty()
        self._task = _TASKS[difficulty]
        return self._task

    def advance_turn(self) -> int:
        self._turn += 1
        return self._turn

    def is_done(self, reward: float, correct: bool) -> bool:
        if not self._task:
            return True

        if self._turn >= self._task.max_turns:
            return True

        if self._task.done_on_first and correct:
            return True

        return False

    def _sample_difficulty(self) -> Difficulty:
        difficulties = list(self._weights.keys())
        weights = list(self._weights.values())
        return self._rng.choices(difficulties, weights=weights, k=1)[0]

    @property
    def current_difficulty(self) -> Difficulty:
        return self._task.difficulty if self._task else "easy"

    @property
    def episode(self) -> int:
        return self._episode


    @property
    def turn(self) -> int:
        return self._turn