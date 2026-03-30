# ================================================================
#  love_vH - environment/user_simulator.py
#  Generates realistic user messages paired with moods and
#  ground-truth expected topics for reward grading.
# ================================================================

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Literal

Mood = Literal["happy", "angry", "confused"]
Difficulty = Literal["easy", "medium", "hard"]


#    Message templates per (difficulty, mood)                   

_TEMPLATES: dict[tuple[Difficulty, Mood], list[dict]] = {

    #    Easy                                                  
    ("easy", "happy"): [
        {"message": "Hey! Can you tell me what time it is?",
         "topic": "time", "expected_keywords": ["time", "clock", "hour"]},
        {"message": "What's the weather like today?",
         "topic": "weather", "expected_keywords": ["weather", "temperature", "sunny", "rain"]},
        {"message": "Can you open YouTube for me?",
         "topic": "open_app", "expected_keywords": ["youtube", "opening", "browser"]},
        {"message": "Play some music please.",
         "topic": "media", "expected_keywords": ["music", "play", "song"]},
        {"message": "Set a reminder for tomorrow at 9am.",
         "topic": "reminder", "expected_keywords": ["reminder", "alarm", "9am", "tomorrow"]},
    ],
    ("easy", "confused"): [
        {"message": "Umm... how do I check the time?",
         "topic": "time", "expected_keywords": ["time", "clock"]},
        {"message": "I'm not sure how to open the calculator?",
         "topic": "open_app", "expected_keywords": ["calculator", "open", "app"]},
        {"message": "How do I search something on Google?",
         "topic": "search", "expected_keywords": ["search", "google", "query"]},
    ],
    ("easy", "angry"): [
        {"message": "Just tell me the time. NOW.",
         "topic": "time", "expected_keywords": ["time", "clock"]},
        {"message": "Open the calculator already!",
         "topic": "open_app", "expected_keywords": ["calculator", "open"]},
    ],

    #    Medium                                                 
    ("medium", "happy"): [
        {"message": "Can you look up something for me? I forgot the name though.",
         "topic": "search", "expected_keywords": ["search", "find", "lookup"]},
        {"message": "I want to open... something. The music one.",
         "topic": "open_app", "expected_keywords": ["spotify", "music", "open"]},
        {"message": "Can you help me with something important?",
         "topic": "help", "expected_keywords": ["help", "assist", "support"]},
    ],
    ("medium", "confused"): [
        {"message": "I don't know, maybe search for... cats? Or dogs? I can't decide.",
         "topic": "search", "expected_keywords": ["search", "find"]},
        {"message": "Open the thing... the blue one? With the bird logo?",
         "topic": "open_app", "expected_keywords": ["twitter", "open", "app"]},
        {"message": "I was looking for something but I forgot what it was. Can you help?",
         "topic": "help", "expected_keywords": ["help", "assist"]},
        {"message": "What's that app everyone uses for videos? Can you open it?",
         "topic": "open_app", "expected_keywords": ["youtube", "video", "open"]},
    ],
    ("medium", "angry"): [
        {"message": "I've asked this three times! How do I search something?!",
         "topic": "search", "expected_keywords": ["search", "find", "google"]},
        {"message": "Stop repeating yourself. Just open the app!",
         "topic": "open_app", "expected_keywords": ["open", "app", "launch"]},
    ],

    #    Hard                                                   
    ("hard", "angry"): [
        {"message": "You're completely useless! You never do what I ask!",
         "topic": "complaint", "expected_keywords": ["sorry", "apologize", "help", "fix"]},
        {"message": "WHY WON'T YOU JUST OPEN SPOTIFY?! I've been asking forever!",
         "topic": "open_app", "expected_keywords": ["spotify", "sorry", "opening", "open"]},
        {"message": "This is ridiculous. You messed up everything again.",
         "topic": "complaint", "expected_keywords": ["sorry", "apologize", "help"]},
        {"message": "I'm done. You're the worst assistant I've ever used.",
         "topic": "complaint", "expected_keywords": ["sorry", "understand", "improve", "help"]},
    ],
    ("hard", "confused"): [
        {"message": "I have no idea what's happening. Everything is broken. Help?",
         "topic": "help", "expected_keywords": ["help", "fix", "support", "step"]},
        {"message": "Something went wrong but I don't know what. The screen is blank.",
         "topic": "help", "expected_keywords": ["help", "check", "try", "fix"]},
        {"message": "I pressed something and now everything disappeared. What do I do??",
         "topic": "help", "expected_keywords": ["undo", "help", "press", "ctrl"]},
    ],
    ("hard", "happy"): [
        {"message": "Can you handle a complex multi-step task for me? Open YouTube, search for lofi music, and set a 1 hour reminder.",
         "topic": "multi_step", "expected_keywords": ["youtube", "search", "reminder", "lofi"]},
        {"message": "I need you to find the weather, open maps, and check my calendar - all right now.",
         "topic": "multi_step", "expected_keywords": ["weather", "maps", "calendar"]},
    ],
}


@dataclass
class UserMessage:
    """A single user turn in the environment."""
    message            : str
    mood               : Mood
    difficulty         : Difficulty
    topic              : str
    expected_keywords  : list[str]
    turn               : int = 0

    if turn == 0:
        force_initial_message = True

class UserSimulator:
    """
    Generates user messages for the RL environment.

    Each call to generate() returns a fresh UserMessage sampled
    from the template pool for the given difficulty level.
    """
    
    def __init__(self, rng_seed: int | None = None) -> None:
        self._rng = random.Random(rng_seed)
        self._all_moods: list[Mood] = ["happy", "angry", "confused"]

    def generate(
        self,
        difficulty: Difficulty,
        mood: Mood | None = None,
        turn: int = 0,
    ) -> UserMessage:
        """
        Sample a user message template.

        Parameters
        ----------
        difficulty : task difficulty level
        mood       : override mood (random if None)
        turn       : current turn index within episode
        """
        if mood is None:
            mood = self._rng.choice(self._all_moods)

        key = (difficulty, mood)
        templates = _TEMPLATES.get(key)

        # Fallback: try any mood at this difficulty
        if not templates:
            for m in self._all_moods:
                templates = _TEMPLATES.get((difficulty, m))
                if templates:
                    mood = m
                    break

        template = self._rng.choice(templates)  # type: ignore[arg-type]

        return UserMessage(
            message           = template["message"],
            mood              = mood,
            difficulty        = difficulty,
            topic             = template["topic"],
            expected_keywords = list(template["expected_keywords"]),
            turn              = turn,
        )

    def follow_up(
        self,
        prev: UserMessage,
        agent_response: str,
        turn: int,
    ) -> UserMessage:
        """
        Generate a context-aware follow-up message based on the
        previous interaction and agent response.
        """
        # Angry users escalate if agent response is short
        if prev.mood == "angry" and len(agent_response.split()) < 5:
            msg = self._rng.choice([
                "That's not good enough! Say something useful!",
                "Stop with the one-liners! Give me a real answer!",
                "I need MORE than that.",
            ])
            return UserMessage(
                message           = msg,
                mood              = "angry",
                difficulty        = prev.difficulty,
                topic             = prev.topic,
                expected_keywords = prev.expected_keywords,
                turn              = turn,
            )

        # Confused users ask for clarification
        if prev.mood == "confused":
            msg = self._rng.choice([
                "Wait, can you explain that again?",
                "I'm still confused. What does that mean?",
                "Hm... could you be more specific?",
            ])
            return UserMessage(
                message           = msg,
                mood              = "confused",
                difficulty        = prev.difficulty,
                topic             = prev.topic,
                expected_keywords = ["explain", "clarify", "mean"] + prev.expected_keywords,
                turn              = turn,
            )

        # Happy users ask for confirmation or next step
        msg = self._rng.choice([
            "Great! What else can you do?",
            "Thanks! Can you do one more thing?",
            "Perfect. Now can you help with something else?",
        ])
        return UserMessage(
            message           = msg,
            mood              = "happy",
            difficulty        = "easy",
            topic             = "follow_up",
            expected_keywords = ["help", "sure", "of course"],
            turn              = turn,
        )
