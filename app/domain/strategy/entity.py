from dataclasses import dataclass
from enum import Enum
from typing import Optional


class StrategyId(str, Enum):
    GOLDEN_CROSS = "golden-cross"  # MA5/MA20 골든크로스
    RSI          = "rsi"           # RSI 과매수/과매도
    BOLLINGER    = "bollinger"     # 볼린저밴드 돌파


class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass(frozen=True)
class Strategy:
    """매매 전략 정의"""
    id: StrategyId
    name: str
    description: str


@dataclass(frozen=True)
class Signal:
    """매매 시그널"""
    strategy_id: str
    stock_code: str
    signal_type: SignalType
    generated_at: str    # ISO 8601
    reason: Optional[str] = None
