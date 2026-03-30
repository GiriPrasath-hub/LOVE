# ================================================================
#  love_vH - reward/human_feedback.py
#  Simulated human/judge feedback system
# ================================================================

from __future__ import annotations
from typing import Any


class HumanFeedback:
    """
    Simulates a human judge scoring responses.
    Returns bonus/penalty based on response quality.
    """

    def evaluate(self, response: str, user_msg: Any) -> float:
        response = response.lower()
        mood = getattr(user_msg, "mood", "happy")

        score = 0.0

        #    Reward clarity                              
        if len(response.split()) > 6:
            score += 1.5

        #    Penalize vague responses                    
        vague_words = ["maybe", "something", "try again", "not sure"]
        if any(w in response for w in vague_words):
            score -= 2

        #    Reward empathy for angry users              
        if mood == "angry":
            if "sorry" in response or "apologize" in response:
                score += 2
            else:
                score -= 2

        #    Penalize repetition                         
        if response.count("let me help") > 1:
            score -= 1.5

        return score