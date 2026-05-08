from dataclasses import dataclass, field

from app.domain.order.entity import OrderType


@dataclass(frozen=True)
class PlaceOrderCommand:
    stock_code: str
    order_type: OrderType
    quantity: int
    price: int = field(default=0)  # 0 = 시장가


@dataclass(frozen=True)
class CancelOrderCommand:
    order_id: str
