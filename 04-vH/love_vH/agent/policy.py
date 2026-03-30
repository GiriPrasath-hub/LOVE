from __future__ import annotations
import random
from typing import Any, Literal

Tone = Literal["friendly", "helpful", "formal"]


# ================================================================
#  Rule-based Policy (base behavior)
# ================================================================

class Policy:

    def select_tone(self, state: dict[str, Any]) -> Tone:
        mood       = state.get("mood", "happy")
        difficulty = state.get("difficulty", "easy")
        context    = state.get("context", [])
        topic      = state.get("topic", "")

        if mood == "angry":
            return "helpful"

        if topic == "complaint":
            return "helpful"

        if mood == "confused":
            return "helpful"

        if difficulty == "hard":
            return "helpful"

        if context:
            recent = context[-3:]
            rewards = [t.get("reward", 0) for t in recent]

            if rewards and (sum(rewards) / len(rewards)) < 2:
                return "helpful"

            responses = [t.get("action", {}).get("response", "") for t in recent]
            if len(set(responses)) <= 1:
                return "helpful"

        if difficulty == "medium":
            return "friendly"

        return "friendly"


# ================================================================
#  Learning Policy (RL-style improvement)
# ================================================================

class LearningPolicy:

    def __init__(self):
        self.stats = {}  # {(topic, tone): {"total": float, "count": int}}
        self.epsilon = 0.3  # exploration rate
        self.min_epsilon = 0.05
        self.decay=0.97

    def update(self, topic: str, tone: str, reward: float):
        key = (topic, tone)

        if key not in self.stats:
            self.stats[key] = {"total": 0.0, "count": 0}

        self.stats[key]["total"] = (self.stats[key]["total"] * 0.9) + reward
        self.stats[key]["count"] += 1

    def get_best_tone(self, topic: str, default="friendly") -> str:

        
        self.epsilon = max(self.min_epsilon, self.epsilon * self.decay)

        
        if random.random() < self.epsilon:
            return random.choice(["friendly", "helpful", "formal"])

        
        best_tone = default
        best_score = float("-inf")

        for (t, tone), data in self.stats.items():

            if t != topic or data["count"] == 0:
                continue

            avg = data["total"] / data["count"]

            if avg > best_score:
                best_score = avg
                best_tone = tone

        return best_tone