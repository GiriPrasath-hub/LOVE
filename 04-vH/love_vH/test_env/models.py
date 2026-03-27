from pydantic import BaseModel


class TestAction(BaseModel):
    message: str
    scenario: str | None = None   # 🔥 ADD THIS


class TestObservation(BaseModel):
    echoed_message: str
    message_length: int
    done: bool
    reward: float