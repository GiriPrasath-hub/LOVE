from __future__ import annotations
from typing import Any

from reward.human_feedback import HumanFeedback
from core.config import EnvConfig, CFG
from reward.accuracy_checker import AccuracyChecker
from reward.relevance_checker import RelevanceChecker
from reward.tone_analyzer import ToneAnalyzer


class RewardSystem:
    def __init__(self, config: EnvConfig | None = None) -> None:
        self.cfg = config or CFG
        self._accuracy = AccuracyChecker()
        self._relevance = RelevanceChecker()
        self._tone = ToneAnalyzer()
        self._human = HumanFeedback()

    def compute(self, action: dict[str, Any], user_msg: Any, context: list[dict]) -> dict[str, Any]:

        response = str(action.get("response", ""))
        tone = str(action.get("tone", "friendly"))

        # Length bonus
        length_bonus = 1.5 if len(response.split()) > 8 else 0.0

        # Sub checks
        acc = self._accuracy.check(
            response=response,
            expected_keywords=user_msg.expected_keywords,
            topic=user_msg.topic,
        )

        rel = self._relevance.check(
            response=response,
            topic=getattr(user_msg, "topic", "default"),
        )

        ton = self._tone.analyze(
            response=response,
            tone=tone,
            user_mood=getattr(user_msg, "mood", "happy"),
        )

        human_score = self._human.evaluate(response, user_msg)

        # Accuracy
        accuracy_reward = 15 if acc.get("correct") else (6 if acc.get("partial") else -12)

        # Relevance
        relevance_reward = 10 if rel.get("relevant") else (5 if rel.get("partial") else -5)

        # Tone
        tone_quality = ton.get("quality", "neutral")
        user_mood = getattr(user_msg, "mood", "happy")

        if tone_quality == "good":
            tone_reward = 6 + (2 if user_mood == "angry" else 0)
        elif tone_quality == "neutral":
            tone_reward = -2 if user_mood == "angry" else 0
        else:
            tone_reward = -8

        # Repetition penalty
        repetition_penalty = 0
        if context:
            last_response = str(context[-1].get("action", {}).get("response", "")).strip()
            if response.strip() == last_response:
                repetition_penalty = -5

        # Follow-up penalty
        followup_penalty = 0
        if getattr(user_msg, "topic", "") == "follow_up":
            if "what else" in response.lower():
                followup_penalty = -3

        total_penalty = repetition_penalty + followup_penalty

        total = (
            accuracy_reward
            + relevance_reward
            + tone_reward
            + total_penalty
            + length_bonus
            + human_score
        )

        return {
            "total": round(total, 2),
            "correct": acc.get("correct", False),
            "accuracy_score": 1.0 if acc.get("correct") else (0.5 if acc.get("partial") else 0.0),
            "accuracy_reward": accuracy_reward,
            "relevance_reward": relevance_reward,
            "tone_reward": tone_reward,
            "human_feedback": human_score,
            "repetition_penalty": repetition_penalty,
            "followup_penalty": followup_penalty,
            "length_bonus": length_bonus,
        }