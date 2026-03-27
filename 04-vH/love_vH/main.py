#!/usr/bin/env python3
# ================================================================
#  love_vH — main.py
#  Entry point.  Initialises environment and agent, runs the
#  training loop, and prints final results.
#
#  Run:  python main.py
# ================================================================

from __future__ import annotations

import sys
import os

# Ensure project root is on the path when run directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import CFG
from core.controller import Controller


def print_header() -> None:
    bar = "=" * 72
    print(bar)
    print("  LOVE vH — Hackathon Edition")
    print("  OpenEnv-Compatible RL Environment for AI Assistant Training")
    print(bar)
    print(f"  Episodes      : {CFG.num_episodes}")
    print(f"  Max steps/ep  : {CFG.max_steps_per_episode}")
    print(f"  Difficulties  : {CFG.difficulty_weights}")
    print(f"  Log file      : {CFG.log_path}")
    print(bar)
    print()


def print_final(summary: dict) -> None:
    bar = "=" * 72
    print(f"\n{bar}")
    print("  KEY RESULTS")
    print(bar)
    print(f"  Total interactions   : {summary.get('total_interactions', 0)}")
    print(f"  Total episodes       : {summary.get('total_episodes', 0)}")
    print(f"  Avg reward / turn    : {summary.get('avg_reward_per_turn', 0):+.3f}")
    print(f"  Avg reward / episode : {summary.get('avg_episode_reward', 0):+.3f}")
    print(f"  Accuracy rate        : {summary.get('accuracy_rate', 0):.1%}")
    print(f"  Mood distribution    : {summary.get('mood_distribution', {})}")
    worst = summary.get("worst_topics", [])
    if worst:
        print(f"  Lowest-scoring topics:")
        for topic, avg in worst:
            print(f"    {topic:<20s}: avg reward = {avg:+.2f}")
    print(bar)


def main() -> None:
    print_header()

    ctrl = Controller(config=CFG)
    summary = ctrl.run()

    print_final(summary)


if __name__ == "__main__":
    main()
