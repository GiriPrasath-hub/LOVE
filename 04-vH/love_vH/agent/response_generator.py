# ================================================================
#  love_vH — agent/response_generator.py
#  Rule-based response generator.  No external API required.
#  Produces realistic assistant responses from template pools.
# ================================================================

from __future__ import annotations

import random
from typing import Any


# ── Response templates per topic ──────────────────────────────

_RESPONSES: dict[str, list[str]] = {
    "time": [
        "The current time is {time}. Let me know if you need anything else!",
        "It's {time} right now. Happy to help with more!",
        "Right now it's {time}. Can I assist with something else?",
    ],
    "weather": [
        "The weather today looks partly cloudy with a high of 22°C. Should be a nice day!",
        "Current conditions: sunny with light winds, around 24°C. Great day to be outside!",
        "Looks like there's a chance of rain this afternoon, temperatures around 18°C.",
    ],
    "open_app": [
        "Opening {app} for you right now!",
        "Sure! Opening {app} now.",
        "Of course! Starting {app} right away.",
        "I'm opening {app} for you. Let me know if you need anything else.",
    ],
    "search": [
        "Searching Google for that right now. I'll bring up the results for you!",
        "Of course! Let me find that for you on Google.",
        "Sure, I'll search for that immediately. Here are the top results!",
        "Happy to search for that! Opening search results now.",
    ],
    "media": [
        "Playing your music now! Enjoy the tunes.",
        "Of course! I'm queuing up some music for you.",
        "Starting playback right away! Let me know if you'd like to change the track.",
    ],
    "reminder": [
        "Done! I've set your reminder. I'll alert you at the scheduled time.",
        "Your reminder is set! I'll notify you when the time comes.",
        "Reminder created successfully! You'll get a notification at that time.",
    ],
    "complaint": [
        "I'm really sorry about that! I understand your frustration and I want to help fix this. What can I do?",
        "You're absolutely right to be upset, and I sincerely apologize. Let me make this right for you.",
        "I'm sorry I haven't met your expectations. I'm here to help and I'll do better. What do you need?",
        "I completely understand your frustration. I apologize for the trouble — let me fix this right away.",
    ],
    "help": [
        "Of course! Let me help you step by step. First, let's try restarting the application.",
        "I'm here to help! Let me walk you through the solution. Can you describe what you see?",
        "Sure, let's fix this together! Try pressing Ctrl+Z to undo your last action.",
        "Happy to assist! Let me guide you through this. What exactly is happening on your screen?",
    ],
    "multi_step": [
        "Sure! I'll do this step-by-step:\n1. Opening YouTube\n2. Playing music\n3. Setting reminder",
        "Here’s what I’m doing:\n• Checking weather\n• Opening Maps\n• Updating your schedule",
    ],
    "follow_up": [
        "Sure! I can help with many things like search, apps, reminders. What do you need?",
        "I can assist with tasks, apps, and information. Tell me what you'd like!",
    ],
    "default": [
        "I'm here to help! Could you give me a bit more detail so I can assist you better?",
        "Of course! Let me take care of that for you right away.",
        "Sure! Happy to help. Let me know exactly what you need.",
        "I understand. Let me work on that for you!",
    ],
}

# ── Tone prefixes ─────────────────────────────────────────────

_TONE_PREFIX: dict[str, list[str]] = {
    "friendly": ["Hey! ", "Sure! ", "Of course! ", "Alright! ", ""],
    "helpful" : ["Happy to help! ", "Let me assist you. ", "Here to help! ", "Let's solve this together. ", ""],
    "formal"  : ["Certainly. ", "Understood. ", "I will handle that. ", "Proceeding now. ", ""],
}

# ── App name extraction hints ─────────────────────────────────

_APP_HINTS: dict[str, str] = {
    "youtube"   : "YouTube",
    "spotify"   : "Spotify",
    "chrome"    : "Chrome",
    "calculator": "Calculator",
    "vscode"    : "VS Code",
    "vs code"   : "VS Code",
    "maps"      : "Google Maps",
    "twitter"   : "Twitter",
    "discord"   : "Discord",
    "whatsapp"  : "WhatsApp",
}

import datetime


class ResponseGenerator:
    """
    Generates rule-based assistant responses given a state and tone.

    No external API — uses template expansion with light context
    awareness (extracts app names, handles moods, etc.).
    """

    def __init__(self, rng_seed: int | None = None) -> None:
        self._rng = random.Random(rng_seed)
        self._last_response = None

    def generate(
        self,
        state : dict[str, Any],
        tone  : str,
    ) -> str:
        """
        Generate a response string for the given state and tone.

        Parameters
        ----------
        state : environment state dict
        tone  : "friendly" | "formal" | "helpful"

        Returns
        -------
        str : the generated response text
        """
        topic    = state.get("topic", "default")
        message  = state.get("user_message", "")
        mood     = state.get("mood", "happy")

        # Choose template pool
        templates = _RESPONSES.get(topic, _RESPONSES["default"])
        template = self._rng.choice(templates)
        if template == self._last_response and len(templates) > 1:
            template = self._rng.choice([t for t in templates if t != template])
        self._last_response = template

        # Fill slots
        response = self._fill_slots(template, message, mood)

        # Prepend tone prefix
        prefix    = self._rng.choice(_TONE_PREFIX.get(tone, [""]))
        if prefix and not response.startswith(prefix.strip()):
            response = prefix + response

        # Add slight variation for realism
        if self._rng.random() < 0.2:
            response += " Let me know if you need anything else."

        if mood == "angry":
            tone = "formal"
        elif mood == "confused":
            tone = "helpful"

        return response

    def _fill_slots(self, template: str, message: str, mood: str) -> str:
        """Replace {slot} placeholders in the template."""
        msg_lower = message.lower()

        # {time}
        if "{time}" in template:
            now = datetime.datetime.now().strftime("%I:%M %p")
            template = template.replace("{time}", now)

        # {app}
        if "{app}" in template:
            app_name = "the app"
            for hint, label in _APP_HINTS.items():
                if hint in msg_lower:
                    app_name = label
                    break
            template = template.replace("{app}", app_name)

        # Improve response for angry users
        if mood == "angry":
            if "sorry" not in template.lower():
                template = "I'm sorry for the inconvenience. " + template

        return template
