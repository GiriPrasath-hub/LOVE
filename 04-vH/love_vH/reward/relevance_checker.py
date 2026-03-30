# ================================================================
#  love_vH - reward/relevance_checker.py
#  Checks whether the agent's response is relevant to the
#  user's topic, even if not perfectly correct.
# ================================================================

from __future__ import annotations


#    Topic -> relevance signal words                             

_TOPIC_SIGNALS: dict[str, list[str]] = {
    "time"       : ["time", "clock", "hour", "minute", "it's", "currently"],
    "weather"    : ["weather", "temperature", "sunny", "rain", "cloud", "forecast"],
    "open_app"   : ["opening", "open", "launching", "launch", "app", "started"],
    "search"     : ["search", "searching", "found", "result", "google", "look"],
    "media"      : ["play", "playing", "music", "song", "track", "queue"],
    "reminder"   : ["reminder", "alarm", "set", "remind", "notification"],
    "complaint"  : ["sorry", "apologize", "understand", "improve", "help", "fix"],
    "help"       : ["help", "assist", "try", "fix", "step", "let me", "here"],
    "multi_step" : ["open", "search", "reminder", "set", "launching", "found"],
    "follow_up"  : ["sure", "of course", "help", "happy", "what", "next"],
}

_GENERIC_SIGNALS = ["i", "you", "the", "and", "here", "let", "will"]


class RelevanceChecker:
    """
    Determines whether the agent's response is on-topic.

    Scoring
    -------
    relevant     -> +8   (response contains topic signals)
    not relevant -> +0   (no topic signals found)

    Note: relevance does NOT imply correctness - a response can be
    relevant (mentions right domain) but still wrong (wrong answer).
    """

    def __init__(self, min_signal_hits: int = 1) -> None:
        self._min_hits = min_signal_hits

    def check(
        self,
        response : str,
        topic    : str,
    ) -> dict:
        """
        Returns dict with keys: relevant (bool), signal_hits (int),
        matched_signals (list).
        """
        response_lower = response.lower()
        signals        = _TOPIC_SIGNALS.get(topic, [])

        matched = [s for s in signals if s in response_lower]
        hits    = len(matched)

        # Generic fallback: if no topic signals but response is substantive
        if hits == 0 and len(response.split()) >= 6:
            generic_hits = sum(1 for g in _GENERIC_SIGNALS if g in response_lower)
            relevant = generic_hits >= 3
        else:
            relevant = hits >= self._min_hits

        return {
            "relevant"       : relevant,
            "signal_hits"    : hits,
            "matched_signals": matched,
            "topic"          : topic,
        }
