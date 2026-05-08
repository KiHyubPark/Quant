from pydantic import BaseModel


class StockSchema(BaseModel):
    code: str
    name: str
    market: str


class CandleSchema(BaseModel):
    date: str
    open: int
    high: int
    low: int
    close: int
    volume: int


class TickerSchema(BaseModel):
    code: str
    price: int
    change: int
    change_rate: float
