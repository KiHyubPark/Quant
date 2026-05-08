from pydantic import BaseModel, Field

from app.domain.order.entity import OrderStatus, OrderType


class PlaceOrderSchema(BaseModel):
    stock_code: str
    order_type: OrderType = Field(..., description="BUY 또는 SELL")
    quantity: int = Field(..., gt=0)
    price: int = Field(default=0, ge=0, description="0이면 시장가")


class OrderResponseSchema(BaseModel):
    order_id: str
    stock_code: str
    order_type: OrderType
    quantity: int
    price: int
    status: OrderStatus
    created_at: str


class TradeSchema(BaseModel):
    trade_id: str
    order_id: str
    stock_code: str
    order_type: OrderType
    quantity: int
    price: int
    traded_at: str
