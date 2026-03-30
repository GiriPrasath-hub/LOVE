# ================================================================
#  love_vH - api/openenv_adapter.py
#  Wraps LoveEnv with strict OpenEnv / OpenAI Gym-compatible
#  interface validation and introspection.
#
#  Guarantees
#            
#    reset() always returns a dict state
#    step(action) always returns exactly (state, float, bool, dict)
#    action format is validated before dispatch
#    observation and action space metadata exposed as attributes
# ================================================================

from __future__ import annotations

from typing import Any

from environment.env import LoveEnv
from core.config import EnvConfig, CFG


class Space:
    """Minimal space descriptor (mirrors gym.spaces interface)."""

    def __init__(self, keys: list[str], description: str = "") -> None:
        self.keys        = keys
        self.description = description

    def contains(self, x: dict) -> bool:
        """Return True if x contains all required keys."""
        return isinstance(x, dict) and all(k in x for k in self.keys)

    def __repr__(self) -> str:
        return f"DictSpace(keys={self.keys})"


class OpenEnvAdapter:
    """
    OpenEnv-compatible wrapper around LoveEnv.

    Conforms to the standard interface:
        reset()      state: dict
        step(action) (state, reward: float, done: bool, info: dict)
        render()
        close()

    Also exposes:
        observation_space : Space
        action_space      : Space
        metadata          : dict

    Parameters
    ----------
    env : LoveEnv instance to wrap (creates one if None)
    cfg : EnvConfig (used only if env is None)
    """

    def __init__(
        self,
        env : LoveEnv | None = None,
        cfg : EnvConfig | None = None,
    ) -> None:
        self._cfg = cfg or CFG
        self._env = env or LoveEnv(self._cfg)

        self.observation_space = Space(
            keys        = ["user_message", "mood", "difficulty", "turn", "context"],
            description = "Current user message, mood, difficulty level, turn index, and history.",
        )
        self.action_space = Space(
            keys        = ["response", "tone"],
            description = "Agent text response and tone (friendly | helpful | formal).",
        )
        self.metadata = {
            "version"         : "vH",
            "name"            : "LoveEnv-v0",
            "reward_range"    : (-22.0, +23.0),
            "max_episode_steps": self._cfg.max_steps_per_episode,
        }
        self._episode_count = 0
        self._step_count    = 0

    #    OpenEnv interface                                      

    def reset(self) -> dict[str, Any]:
        """
        Reset the environment and return the initial observation.

        Returns
        -------
        state : dict matching observation_space.keys
        """
        self._episode_count += 1
        state = self._env.reset()
        self._validate_state(state, context="reset()")
        return state

    def step(self, action: dict[str, Any]) -> tuple[dict, float, bool, dict]:
        """
        Take one step in the environment.

        Parameters
        ----------
        action : dict with keys "response" (str) and "tone" (str)

        Returns
        -------
        (next_state, reward, done, info)

        Raises
        ------
        AssertionError : if action does not conform to action_space
        """
        self._validate_action(action)

        result = self._env.step(action)

        assert len(result) == 4, (
            f"env.step() must return 4 values, got {len(result)}"
        )
        next_state, reward, done, info = result

        assert isinstance(reward, (int, float)), (
            f"reward must be numeric, got {type(reward)}"
        )
        assert isinstance(done, bool), (
            f"done must be bool, got {type(done)}"
        )
        assert isinstance(info, dict), (
            f"info must be dict, got {type(info)}"
        )
        self._validate_state(next_state, context="step() -> next_state")

        self._step_count += 1
        return next_state, float(reward), done, info

    def render(self, mode: str = "text") -> None:
        """Render the current environment state."""
        self._env.render(mode)

    def close(self) -> None:
        """Release environment resources."""
        self._env.close()

    #    Introspection                                          

    @property
    def unwrapped(self) -> LoveEnv:
        """Return the underlying LoveEnv without the adapter."""
        return self._env

    @property
    def episode_count(self) -> int:
        return self._episode_count

    @property
    def step_count(self) -> int:
        return self._step_count

    def __repr__(self) -> str:
        return (
            f"OpenEnvAdapter(env=LoveEnv, "
            f"episodes={self._episode_count}, "
            f"steps={self._step_count})"
        )

    #    Validation helpers                                     

    def _validate_action(self, action: Any) -> None:
        assert isinstance(action, dict), (
            f"action must be a dict, got {type(action).__name__}"
        )
        for key in self.action_space.keys:
            assert key in action, (
                f"action missing required key '{key}'. "
                f"Required: {self.action_space.keys}"
            )
        valid_tones = {"friendly", "helpful", "formal"}
        tone = action.get("tone", "")
        assert tone in valid_tones, (
            f"action['tone'] must be one of {valid_tones}, got '{tone}'"
        )
        assert isinstance(action.get("response", ""), str), (
            "action['response'] must be a string"
        )

    def _validate_state(self, state: Any, context: str = "") -> None:
        assert isinstance(state, dict), (
            f"[{context}] state must be dict, got {type(state).__name__}"
        )
        for key in self.observation_space.keys:
            assert key in state, (
                f"[{context}] state missing key '{key}'"
            )
