from dataclasses import dataclass
from enum import Enum
from typing import Optional


class OrderType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    PENDING = "PENDING"      # 주문 대기
    FILLED = "FILLED"        # 체결 완료
    CANCELLED = "CANCELLED"  # 취소


@dataclass(frozen=True)
class Order:
    """주문"""
    order_id: str
    stock_code: str
    order_type: OrderType
    quantity: int
    price: int               # 0이면 시장가
    status: OrderStatus
    created_at: str          # ISO 8601


@dataclass(frozen=True)
class Trade:
    """체결 내역"""
    trade_id: str
    order_id: str
    stock_code: str
    order_type: OrderType
    quantity: int
    price: int
    traded_at: str
