# ================================================================
#  love_vH — reward/tone_analyzer.py
#  Evaluates whether the agent's chosen tone matches the
#  user's mood and the situation.
# ================================================================

from __future__ import annotations


# ── Tone-mood compatibility matrix ────────────────────────────
# Maps (agent_tone, user_mood) → "good" | "neutral" | "bad"

_COMPAT: dict[tuple[str, str], str] = {
    # friendly tone
    ("friendly", "happy")   : "good",
    ("friendly", "confused") : "good",
    ("friendly", "angry")   : "neutral",   # friendly alone isn't enough for anger

    # helpful tone
    ("helpful", "happy")    : "good",
    ("helpful", "confused") : "good",
    ("helpful", "angry")    : "good",      # helpful is best for angry users

    # formal tone
    ("formal", "happy")     : "neutral",
    ("formal", "confused")  : "bad",       # formal confuses confused users more
    ("formal", "angry")     : "neutral",
}

# Positive language patterns that boost any tone
_POSITIVE_PATTERNS = [
    "of course", "happy to", "sure", "let me", "i can",
    "i'll", "absolutely", "no problem", "right away", "here",
]

# Negative language patterns that hurt tone score
_NEGATIVE_PATTERNS = [
    "can't", "won't", "unable", "impossible", "never",
    "stop asking", "i said", "you're wrong", "incorrect",
]


class ToneAnalyzer:
    """
    Evaluates agent tone quality given the user's mood.

    Scoring
    -------
    "good"    → +5
    "neutral" → +0
    "bad"     → -6
    Additionally adjusted by presence of positive/negative language.
    """

    def analyze(
        self,
        response  : str,
        tone      : str,
        user_mood : str,
    ) -> dict:
        """
        Returns dict with keys: quality (str), score (float), reason (str)
        """
        response_lower = response.lower()
        tone_lower     = tone.lower()
        mood_lower     = user_mood.lower()

        # Base quality from compatibility matrix
        key     = (tone_lower, mood_lower)
        quality = _COMPAT.get(key, "neutral")

        # Language pattern adjustment
        pos_hits = sum(1 for p in _POSITIVE_PATTERNS if p in response_lower)
        neg_hits = sum(1 for p in _NEGATIVE_PATTERNS if p in response_lower)

        adjustment = 0.0
        if pos_hits >= 2:
            adjustment += 1.0
            if quality == "neutral":
                quality = "good"
        if neg_hits >= 1:
            adjustment -= 2.0
            if quality != "bad":
                quality = "neutral" if quality == "good" else "bad"

        # Length check — very short responses are never "good" for hard moods
        if len(response.split()) < 4 and mood_lower in ("angry", "confused"):
            quality     = "bad"
            adjustment -= 1.0

        return {
            "quality"    : quality,
            "tone"       : tone_lower,
            "user_mood"  : mood_lower,
            "pos_hits"   : pos_hits,
            "neg_hits"   : neg_hits,
            "adjustment" : adjustment,
        }
