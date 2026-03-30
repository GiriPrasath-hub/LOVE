# ================================================================
# love_vH - openenv/client.py
# OpenEnv client interface (REQUIRED)
# ================================================================

from typing import Any, Dict
from openenv.environment import OpenEnvWrapper


class Client:
    """
    Standard OpenEnv client interface.
    Used by grader to interact with your environment.
    """

    def __init__(self):
        self.env = OpenEnvWrapper()
        self.state = self.env.reset()

    def reset(self) -> Dict[str, Any]:
        self.state = self.env.reset()
        return self.state

    def step(self, action: Dict[str, Any]) -> Dict[str, Any]:
        state, reward, done, info = self.env.step(action)

        return {
            "state": state,
            "reward": reward,
            "done": done,
            "info": info
        }