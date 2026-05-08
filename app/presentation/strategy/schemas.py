from pydantic import BaseModel

from app.domain.strategy.entity import SignalType


class StrategySchema(BaseModel):
    id: str
    name: str
    description: str


class CreateStrategySchema(BaseModel):
    name: str
    description: str


class SignalSchema(BaseModel):
    strategy_id: str
    stock_code: str
    signal_type: SignalType
    generated_at: str
    reason: str | None = None
