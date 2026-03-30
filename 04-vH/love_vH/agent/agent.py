from __future__ import annotations
from typing import Any

from core.config import EnvConfig, CFG
from agent.policy import Policy, LearningPolicy
from agent.response_generator import ResponseGenerator


class LoveAgent:

    def __init__(self, config: EnvConfig | None = None) -> None:
        self.cfg = config or CFG

        self._base_policy = Policy()           # fallback logic
        self._learning_policy = LearningPolicy()  # RL learning

        self._gen = ResponseGenerator()

        self._step_count = 0
        self._total_reward: float = 0.0

        self.last_action = None


    def act(self, state: dict[str, Any]) -> dict[str, Any]:

        topic = state.get("topic", "default")

        # Learning-based tone
        tone = self._learning_policy.get_best_tone(topic)

        # Fallback safety (important)
        if tone not in ["friendly", "helpful", "formal"]:
            tone = self._base_policy.select_tone(state)

        response = self._gen.generate(state, tone)

        action = {
            "response": response,
            "tone": tone
        }

        # Save for learning
        self.last_action = (topic, tone)

        return action


    def observe_reward(self, reward: float):

        if self.last_action:
            topic, tone = self.last_action
            self._learning_policy.update(topic, tone, reward)

        self._total_reward += reward
        self._step_count += 1
        self.epsilon *= 0.98
        self.epsilon = max(self.epsilon, self.min_epsilon)
    

    def reset_stats(self) -> None:
        self._step_count = 0
        self._total_reward = 0.0


    @property
    def total_reward(self) -> float:
        return self._total_reward

    @property
    def step_count(self) -> int:
        return self._step_count