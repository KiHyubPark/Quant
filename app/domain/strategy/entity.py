from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass(frozen=True)
class Strategy:
    """매매 전략 정의"""
    id: str
    name: str        # 전략명 (예: 골든크로스)
    description: str


@dataclass(frozen=True)
class Signal:
    """매매 시그널"""
    strategy_id: str
    stock_code: str
    signal_type: SignalType
    generated_at: str    # ISO 8601
    reason: Optional[str] = None
