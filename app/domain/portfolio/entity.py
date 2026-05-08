from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Position:
    """보유 포지션"""
    stock_code: str
    stock_name: str
    quantity: int          # 보유 수량
    avg_price: int         # 평균 매수가
    current_price: int     # 현재가
    profit_loss: int       # 평가 손익
    profit_loss_rate: float  # 수익률 (%)


@dataclass(frozen=True)
class Balance:
    """계좌 잔고"""
    cash: int              # 예수금
    total_eval: int        # 총 평가금액
    total_profit_loss: int # 총 손익
    positions: tuple[Position, ...]
