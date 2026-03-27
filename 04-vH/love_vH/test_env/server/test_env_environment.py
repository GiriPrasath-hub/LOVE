from uuid import uuid4
import random

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import TestAction, TestObservation
except ImportError:
    from models import TestAction, TestObservation


class TestEnvironment(Environment):

    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self.current_scenario = None
        self.scenarios = [
            {"situation": "User is angry about a delayed order", "correct_action": "apologize"},
            {"situation": "User is happy with service", "correct_action": "thank"},
            {"situation": "User asks for help with login issue", "correct_action": "assist"}
        ]

    # 🔥 ADVANCED vH
    def vh_evaluate(self, user_action, correct_action):

        user_action = user_action.lower()

        intent_map = {
            "apologize": ["sorry", "apologize", "regret", "my mistake"],
            "thank": ["thank", "thanks", "appreciate", "grateful"],
            "assist": ["help", "assist", "support", "guide", "fix", "resolve"]
        }

        keywords = intent_map.get(correct_action, [])

        score = 0
        matched = []

        for word in keywords:
            if word in user_action:
                score += 1
                matched.append(word)

        # length bonus
        length_bonus = min(len(user_action.split()) * 0.1, 0.5)

        final_score = (score * 0.5) + length_bonus
        final_score = max(-1, min(final_score, 1))

        # explanation
        if final_score >= 0.8:
            feedback = f"🔥 Excellent response!\nMatched: {matched}"
        elif final_score >= 0.5:
            feedback = f"👍 Good response.\nMatched: {matched}"
        elif final_score > 0:
            feedback = f"⚠️ Partial understanding.\nMatched: {matched}"
        else:
            feedback = "❌ Incorrect intent."

        return final_score, feedback

    def reset(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)

        self.current_scenario = random.choice(self.scenarios)

        return TestObservation(
            echoed_message=f"Situation: {self.current_scenario['situation']}",
            message_length=0,
            done=False,
            reward=0.0,
        )

    def step(self, action: TestAction):
        self._state.step_count += 1

        user_action = (action.message or "").lower().strip()

        if not self.current_scenario:
            return TestObservation(
                echoed_message="⚠️ Please reset first",
                message_length=0,
                done=True,
                reward=0.0,
            )

        correct_action = self.current_scenario["correct_action"]

        reward, response = self.vh_evaluate(user_action, correct_action)

        done = True if reward > 0 else False

        return TestObservation(
            echoed_message=response,
            message_length=len(user_action),
            done=done,
            reward=round(reward, 2),
        )

    @property
    def state(self):
        return self._state