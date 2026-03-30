# ================================================================
#  love_vH - logger/logger.py
#  FINAL FIXED VERSION (ACCURACY + CLEAN LOGGING)
# ================================================================

from __future__ import annotations

import datetime
import sys
from typing import Any

from core.config import EnvConfig, CFG


class EpisodeLogger:

    def __init__(self, cfg: EnvConfig | None = None) -> None:
        self.cfg = cfg or CFG
        self._fh = None

        if self.cfg.log_to_file:
            try:
                self._fh = open(self.cfg.log_path, "w", encoding="utf-8")
                self._write(
                    f"# LOVE vH Training Log - "
                    f"started {datetime.datetime.now().isoformat()}\n"
                )
            except OSError as exc:
                print(
                    f"[Logger] Cannot open log file '{self.cfg.log_path}': {exc}",
                    file=sys.stderr,
                )

    #    STEP LOGGING                                              

    def log_step(
        self,
        episode: int,
        state: dict[str, Any],
        action: dict[str, Any],
        reward: float,
        done: bool,
        info: dict[str, Any],
    ) -> None:

        breakdown = info.get("reward_breakdown", {})
        correct = breakdown.get("correct", False)

        user_msg = str(state.get("user_message", ""))[:55]
        response = str(action.get("response", ""))[:55]

        # Safe episode
        try:
            episode = int(episode)
        except:
            episode = 0

        # Safe turn
        turn_raw = info.get("turn", 0)
        while isinstance(turn_raw, dict):
            turn_raw = turn_raw.get("step", turn_raw.get("turn", 0))

        try:
            turn = int(turn_raw)
        except:
            turn = 0

        # Safe difficulty
        difficulty = str(info.get("difficulty", "?"))

        #  FIXED ACCURACY FIELD
        try:
            acc_score = float(breakdown.get("accuracy_score", 0))
        except:
            acc_score = 0.0

        try:
            tone_score = float(breakdown.get("tone_reward", 0))
        except:
            tone_score = 0.0

        line = (
            f"  [Ep{episode:03d} T{turn:01d}] "
            f"diff={difficulty:<6s} "
            f"mood={str(state.get('mood','?')):<8s} "
            f"tone={str(action.get('tone','?')):<8s} "
            f"reward={reward:+6.1f} "
            f"correct={'Y' if correct else 'N'} "
            f"acc={acc_score:.1f} "
            f"tone_score={tone_score:.1f} "
            f"done={'Y' if done else 'N'}\n"
            f"          User:  {user_msg}\n"
            f"          Agent: {response}"
        )

        self._write(line)

    #    EPISODE LOG                                              

    def log_episode(self, episode: int, total_reward: float, difficulty: str) -> None:
        bar = "=" * 72
        stars = "*" * min(int(max(total_reward, 0) / 5), 10)

        self._write(
            f"\n{bar}\n"
            f"  Episode {episode:03d} finished | "
            f"difficulty={difficulty:6s} | "
            f"total_reward={total_reward:+7.2f}  {stars}\n"
            f"{bar}\n"
        )

    #    FINAL SUMMARY                                            

    def log_summary(self, summary: dict[str, Any]) -> None:
        bar = "=" * 72

        self._write(f"\n{bar}")
        self._write("  TRAINING COMPLETE - FINAL SUMMARY")
        self._write(bar)

        for key, val in summary.items():
            if key == "all_episode_rewards":
                continue

            self._write(f"  {key:<32s}: {val}")

        # Reward trend
        rewards = summary.get("all_episode_rewards", [])
        if len(rewards) >= 2:
            mid = len(rewards) // 2
            first = sum(rewards[:mid]) / max(mid, 1)
            second = sum(rewards[mid:]) / max(mid, 1)

            trend = "  IMPROVING" if second > first else "  DECLINING"

            self._write(
                f"\n  Reward trend (1st half avg={first:+.2f} -> "
                f"2nd half avg={second:+.2f}): {trend}"
            )

        self._write(bar)
        self._close()

    #    INTERNAL                                                 

    def _write(self, msg: str) -> None:
        print(msg)
        if self._fh:
            self._fh.write(msg + "\n")
            self._fh.flush()

    def _close(self) -> None:
        if self._fh:
            self._fh.close()
            self._fh = None