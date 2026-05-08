from pydantic import BaseModel


class PositionSchema(BaseModel):
    stock_code: str
    stock_name: str
    quantity: int
    avg_price: int
    current_price: int
    profit_loss: int
    profit_loss_rate: float


class BalanceSchema(BaseModel):
    cash: int
    total_eval: int
    total_profit_loss: int
    positions: list[PositionSchema]
