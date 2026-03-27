# ================================================================
#  love_vH — training/trainer.py
#  Runs the RL training loop: episodes, steps, reward logging.
#
#  Loop structure
#  ──────────────
#  for episode in 1..num_episodes:
#      state = env.reset()
#      while not done:
#          action = agent.act(state)
#          next_state, reward, done, info = env.step(action)
#          agent.observe_reward(reward)
#          memory.store(...)
#          logger.log_step(...)
#          state = next_state
#      logger.log_episode(...)
#  logger.log_summary(...)
# ================================================================

from __future__ import annotations

from typing import Any

from core.config import EnvConfig, CFG
from environment.env import LoveEnv
from agent.agent import LoveAgent
from memory.memory_store import MemoryStore


class Trainer:
    """
    Orchestrates the training loop.

    Parameters
    ----------
    env    : LoveEnv instance
    agent  : LoveAgent instance
    logger : EpisodeLogger instance
    cfg    : EnvConfig
    """

    def __init__(
        self,
        env    : LoveEnv,
        agent  : LoveAgent,
        logger : Any,
        cfg    : EnvConfig | None = None,
    ) -> None:
        self.env    = env
        self.agent  = agent
        self.logger = logger
        self.cfg    = cfg or CFG
        self.memory = MemoryStore()

    # ── Public API ────────────────────────────────────────────

    def run(self) -> dict[str, Any]:
        """
        Execute the full training loop.

        Returns
        -------
        summary : dict of aggregate statistics
        """
        all_episode_rewards: list[float] = []

        for ep in range(1, self.cfg.num_episodes + 1):

            # ── Episode start ─────────────────────────────────
            state = self.env.reset()
            self.agent.reset_stats()
            episode_reward = 0.0
            done           = False

            # ── Step loop ─────────────────────────────────────
            while not done:
                action = self.agent.act(state)

                next_state, reward, done, info = self.env.step(action)

                self.agent.observe_reward(reward)
                episode_reward += reward

                # Store in cross-episode memory
                self.memory.store(
                    episode    = ep,
                    turn       = info.get("turn", 0),
                    difficulty = info.get("difficulty", "unknown"),
                    mood       = state.get("mood", "happy"),
                    topic      = state.get("topic", "default"),
                    user_msg   = state.get("user_message", ""),
                    action     = action,
                    reward     = reward,
                    correct    = info.get("reward_breakdown", {}).get("correct", False),
                )
                # Update logging condition
                if ep <= getattr(self.cfg, "log_steps_limit", 3):
                    self.logger.log_step(ep, state, action, reward, done, info)
                state = next_state

            # ── Episode end ───────────────────────────────────
            self.memory.record_episode_reward(episode_reward)
            all_episode_rewards.append(episode_reward)
            self.logger.log_episode(ep, episode_reward, info["difficulty"])

        # ── Training complete ─────────────────────────────────
        summary = self.memory.summary()
        summary["all_episode_rewards"] = all_episode_rewards
        self.logger.log_summary(summary)
        return summary
