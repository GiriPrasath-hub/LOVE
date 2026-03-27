# ================================================================
#  love_vH — memory/memory_store.py
#  Persistent cross-episode memory store.
#
#  Stores all interactions across episodes and supports:
#  - context retrieval (most recent N turns)
#  - episode history (rewards, difficulties)
#  - pattern detection (recurring moods, failing topics)
# ================================================================

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Interaction:
    """One complete user-agent exchange."""
    episode    : int
    turn       : int
    difficulty : str
    mood       : str
    topic      : str
    user_msg   : str
    response   : str
    tone       : str
    reward     : float
    correct    : bool


class MemoryStore:
    """
    Cross-episode interaction memory.

    Stores all interactions, supports retrieval by episode/topic/mood,
    and computes aggregate statistics the agent can use to improve.
    """

    def __init__(self) -> None:
        self._interactions: list[Interaction] = []
        self._episode_rewards: list[float]    = []
        self._topic_rewards: dict[str, list[float]] = defaultdict(list)
        self._mood_counts:   dict[str, int]          = defaultdict(int)

    # ── Write ─────────────────────────────────────────────────

    def store(
        self,
        episode    : int,
        turn       : int,
        difficulty : str,
        mood       : str,
        topic      : str,
        user_msg   : str,
        action     : dict[str, Any],
        reward     : float,
        correct    : bool,
    ) -> None:
        interaction = Interaction(
            episode    = episode,
            turn       = turn,
            difficulty = difficulty,
            mood       = mood,
            topic      = topic,
            user_msg   = user_msg,
            response   = action.get("response", ""),
            tone       = action.get("tone", "friendly"),
            reward     = reward,
            correct    = correct,
        )
        self._interactions.append(interaction)
        self._topic_rewards[topic].append(reward)
        self._mood_counts[mood] += 1

    def record_episode_reward(self, total_reward: float) -> None:
        self._episode_rewards.append(total_reward)

    # ── Read ──────────────────────────────────────────────────

    def recent(self, n: int = 5) -> list[Interaction]:
        """Return the n most recent interactions."""
        return self._interactions[-n:]

    def by_topic(self, topic: str) -> list[Interaction]:
        return [i for i in self._interactions if i.topic == topic]

    def by_mood(self, mood: str) -> list[Interaction]:
        return [i for i in self._interactions if i.mood == mood]

    def worst_topics(self, top_n: int = 3) -> list[tuple[str, float]]:
        """Return topics sorted by average reward ascending."""
        avgs = {
            t: sum(rewards) / len(rewards)
            for t, rewards in self._topic_rewards.items()
            if rewards
        }
        return sorted(avgs.items(), key=lambda x: x[1])[:top_n]

    # ── Statistics ────────────────────────────────────────────

    def summary(self) -> dict[str, Any]:
        if not self._interactions:
            return {"total_interactions": 0}

        rewards = [i.reward for i in self._interactions]
        correct = sum(1 for i in self._interactions if i.correct)

        return {
            "total_interactions"  : len(self._interactions),
            "total_episodes"      : len(self._episode_rewards),
            "avg_reward_per_turn" : round(sum(rewards) / len(rewards), 3),
            "avg_episode_reward"  : round(
                sum(self._episode_rewards) / len(self._episode_rewards), 3
            ) if self._episode_rewards else 0.0,
            "accuracy_rate"       : round(correct / len(self._interactions), 3),
            "mood_distribution"   : dict(self._mood_counts),
            "worst_topics"        : self.worst_topics(),
        }

    def __len__(self) -> int:
        return len(self._interactions)
