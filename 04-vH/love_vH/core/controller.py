# ================================================================
#  love_vH — core/controller.py
#  Orchestrates environment, agent, and training loop.
#  Provides the single entry-point used by main.py.
# ================================================================

from __future__ import annotations

from core.config import CFG
from environment.env import LoveEnv
from agent.agent import LoveAgent
from training.trainer import Trainer
from logger.logger import EpisodeLogger


class Controller:
    """
    Top-level controller.  Wires all components together and
    exposes a single run() method.
    """

    def __init__(self, config=None) -> None:
        self.cfg     = config or CFG
        self.env     = LoveEnv(self.cfg)
        self.agent   = LoveAgent(self.cfg)
        self.logger  = EpisodeLogger(self.cfg)
        self.trainer = Trainer(self.env, self.agent, self.logger, self.cfg)

    def run(self) -> dict:
        """
        Run the full training loop and return summary statistics.
        """
        return self.trainer.run()
