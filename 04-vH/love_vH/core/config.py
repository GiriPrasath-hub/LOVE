# ================================================================
#  love_vH — core/config.py
#  Central configuration for the entire RL environment.
# ================================================================

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class EnvConfig:
    # Episode settings
    max_steps_per_episode: int = 6
    num_episodes: int = 50

    # Difficulty distribution (must sum to 1.0)
    difficulty_weights: dict[str, float] = field(default_factory=lambda: {
        "easy":   0.40,
        "medium": 0.35,
        "hard":   0.25,
    })

    # Reward shaping
    reward_correct:   float =  10.0
    reward_relevant:  float =   8.0
    reward_good_tone: float =   5.0
    reward_wrong:     float = -10.0
    reward_bad_tone:  float =  -6.0
    reward_no_match:  float =  -3.0   # fallback for irrelevant response

    # Memory
    memory_window: int = 5   # how many past interactions to retain

    # Logging
    log_to_file: bool = True
    log_path: str = "love_vH_run.log"


# Singleton used throughout the project
CFG = EnvConfig()
