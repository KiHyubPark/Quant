from pydantic import BaseModel


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
    signal_type: str
    generated_at: str
    reason: str | None = None
