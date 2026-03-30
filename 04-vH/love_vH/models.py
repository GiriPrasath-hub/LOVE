# ================================================================
# love_vH - models.py
# OpenEnv required schemas
# ================================================================

from pydantic import BaseModel
from typing import Any, Dict


class Action(BaseModel):
    """
    Action sent to environment
    """
    response: str
    tone: str


class Observation(BaseModel):
    """
    Observation returned from environment
    """
    observation: Dict[str, Any]
    reward: float
    done: bool
    info: Dict[str, Any]