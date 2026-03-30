# ================================================================
#  love_vH - reward/accuracy_checker.py
#  Grades whether the agent's response correctly addresses
#  the user's request based on expected keyword matching.
# ================================================================

from __future__ import annotations
from urllib import response


class AccuracyChecker:

    def check(self, response, expected_keywords, topic):
        response = response.lower()

        # Normalize response (VERY IMPORTANT)
        response = response.replace("launching", "open")
        response = response.replace("starting", "open")
        response = response.replace("playing", "play")

        #    If no keywords -> fallback              
        if not expected_keywords:
            if topic in response:
                return {"correct": True, "partial": False}
            return {"correct": False, "partial": False}

        matches = 0

        for kw in expected_keywords:
            kw = kw.lower()

            # Flexible matching
            if kw in response:
                matches += 1
            elif kw == "open" and any(x in response for x in ["open", "launch"]):
                matches += 1
            elif kw == "play" and "play" in response:
                matches += 1

        total = len(expected_keywords)

        #    Decision logic                        
        if matches >= max(1, total * 0.3):
            return {"correct": True, "partial": False}

        elif matches > 0:
            return {"correct": False, "partial": True}

        else:
            return {"correct": False, "partial": False}