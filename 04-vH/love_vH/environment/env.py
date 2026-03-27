# ================================================================
#  love_vH — environment/env.py
#  OpenEnv-compatible RL environment for the LOVE assistant.
#
#  Interface
#  ─────────
#    env.reset()          → state: dict
#    env.step(action)     → (next_state, reward, done, info)
#
#  State schema
#  ─────────────
#    {
#      "user_message"  : str,
#      "mood"          : "happy" | "angry" | "confused",
#      "difficulty"    : "easy"  | "medium" | "hard",
#      "turn"          : int,
#      "context"       : list[dict],   # recent history
#    }
#
#  Action schema
#  ─────────────
#    {
#      "response" : str,
#      "tone"     : "friendly" | "formal" | "helpful",
#    }
# ================================================================

from __future__ import annotations

from typing import Any

from core.config import EnvConfig, CFG
from environment.user_simulator import UserSimulator, UserMessage
from environment.task_manager import TaskManager
from environment.context_engine import ContextEngine, Turn
from reward.reward_system import RewardSystem


class LoveEnv:
    """
    OpenEnv-compatible environment for training an AI assistant.

    Each episode presents a user scenario at a sampled difficulty
    level.  The agent submits text actions; the environment grades
    them, generates follow-up user messages, and returns the
    standard (next_state, reward, done, info) tuple.
    """

    metadata = {"render_modes": ["text"], "version": "vH"}

    def __init__(self, config: EnvConfig | None = None) -> None:
        self.cfg     = config or CFG
        self._sim    = UserSimulator()
        self._tasks  = TaskManager(self.cfg.difficulty_weights)
        self._ctx    = ContextEngine(self.cfg.memory_window)
        self._reward = RewardSystem(self.cfg)

        self._current_user_msg: UserMessage | None = None
        self._done = True

    # ── OpenEnv API ───────────────────────────────────────────

    def reset(self) -> dict[str, Any]:
        """
        Begin a new episode.

        Returns
        -------
        state : dict
            Initial observation for the agent.
        """
        task = self._tasks.new_episode()
        self._ctx.reset()
        self._done = False

        # Generate the first user message for this episode
        self._current_user_msg = self._sim.generate(
            difficulty = task.difficulty,
            turn       = 0,
        )

        return self._build_state(self._current_user_msg, turn=0)

    def step(self, action: dict[str, Any]) -> tuple[dict, float, bool, dict]:
        """
        Advance the environment by one turn.

        Parameters
        ----------
        action : dict with keys "response" (str) and "tone" (str)

        Returns
        -------
        next_state : dict
        reward     : float
        done       : bool
        info       : dict   (diagnostic data — not used for training)
        """
        if self._done:
            raise RuntimeError("Episode is done. Call reset() before step().")
        if self._current_user_msg is None:
            raise RuntimeError("Environment not initialised. Call reset() first.")

        # ── Grade the action ──────────────────────────────────
        result = self._reward.compute(
            action      = action,
            user_msg    = self._current_user_msg,
            context     = self._ctx.get_context(),
        )
        reward  = result["total"]
        correct = result["correct"]

        turn = self._tasks.advance_turn()

        # ── Record in context ─────────────────────────────────
        self._ctx.record(Turn(
            turn_number  = turn,
            user_message = self._current_user_msg.message,
            agent_action = action,
            reward       = reward,
            mood         = self._current_user_msg.mood,
            difficulty   = self._current_user_msg.difficulty,
        ))

        # ── Check done ────────────────────────────────────────
        self._done = self._tasks.is_done(reward, correct)

        # ── Generate next state ───────────────────────────────
        if self._done:
            next_state = self._build_state(self._current_user_msg, turn=turn)
        else:
            self._current_user_msg = self._sim.follow_up(
                prev           = self._current_user_msg,
                agent_response = action.get("response", ""),
                turn           = turn,
            )
            next_state = self._build_state(self._current_user_msg, turn=turn)

        info = {
            "reward_breakdown": result,
            "difficulty"      : self._tasks.current_difficulty,
            "episode"         : self._tasks.episode,
            "turn"            : turn,
            "episode_reward"  : self._ctx.episode_reward,
        }

        return next_state, reward, self._done, info

    # ── Gym-style helpers ─────────────────────────────────────

    def render(self, mode: str = "text") -> None:
        """Print the current state to stdout."""
        if self._current_user_msg:
            print(
                f"[Env] Episode {self._tasks.episode} | "
                f"Turn {self._tasks.turn} | "
                f"Difficulty: {self._tasks.current_difficulty} | "
                f"Mood: {self._current_user_msg.mood}\n"
                f"  User: {self._current_user_msg.message}"
            )

    def close(self) -> None:
        """Clean up resources (no-op here, required by interface)."""
        pass

    @property
    def observation_space_keys(self) -> list[str]:
        return ["user_message", "mood", "difficulty", "turn", "context"]

    @property
    def action_space_keys(self) -> list[str]:
        return ["response", "tone"]

    # ── Internal ──────────────────────────────────────────────

    def _build_state(self, msg: UserMessage, turn: int) -> dict[str, Any]:
        return {
            "user_message" : msg.message,
            "mood"         : msg.mood,
            "difficulty"   : msg.difficulty,
            "topic"        : msg.topic,
            "turn"         : turn,
            "context"      : self._ctx.get_context(),
        }
