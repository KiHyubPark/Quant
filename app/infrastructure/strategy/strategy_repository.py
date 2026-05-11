from datetime import datetime, timezone
from typing import Callable

from app.domain.market_data.entity import CandlePeriod
from app.domain.market_data.repository import MarketDataRepository
from app.domain.strategy.entity import Signal, SignalType, Strategy, StrategyId
from app.domain.strategy.exceptions import StrategyNotFoundError

# 기본 제공 전략 목록
_DEFAULT_STRATEGIES: list[Strategy] = [
    Strategy(
        id=StrategyId.GOLDEN_CROSS,
        name="골든크로스",
        description="MA5가 MA20을 상향 돌파하면 BUY, 하향 돌파하면 SELL",
    ),
    Strategy(
        id=StrategyId.RSI,
        name="RSI",
        description="RSI 14일 기준 30 이하면 BUY(과매도), 70 이상이면 SELL(과매수)",
    ),
    Strategy(
        id=StrategyId.BOLLINGER,
        name="볼린저밴드",
        description="종가가 하단 밴드 아래면 BUY, 상단 밴드 위면 SELL",
    ),
]


# ------------------------------------------------------------------ #
# 전략 계산 함수
# ------------------------------------------------------------------ #

def _moving_average(prices: list[float], period: int) -> float:
    if len(prices) < period:
        raise ValueError(f"가격 데이터가 부족합니다. (필요: {period}, 현재: {len(prices)})")
    return sum(prices[-period:]) / period


def _calc_golden_cross_signal(prices: list[float]) -> tuple[SignalType, str]:
    """MA5 / MA20 골든크로스·데드크로스 판정."""
    if len(prices) < 21:
        raise ValueError("MA20 계산을 위해 최소 21일치 데이터가 필요합니다.")

    today_ma5     = _moving_average(prices, 5)
    today_ma20    = _moving_average(prices, 20)
    yesterday_ma5  = _moving_average(prices[:-1], 5)
    yesterday_ma20 = _moving_average(prices[:-1], 20)

    if today_ma5 > today_ma20 and yesterday_ma5 <= yesterday_ma20:
        signal = SignalType.BUY
    elif today_ma5 < today_ma20 and yesterday_ma5 >= yesterday_ma20:
        signal = SignalType.SELL
    else:
        signal = SignalType.HOLD

    reason = f"MA5={today_ma5:,.0f} / MA20={today_ma20:,.0f} → {signal.value}"
    return signal, reason


def _calc_rsi_signal(prices: list[float]) -> tuple[SignalType, str]:
    """RSI 14일 기준 과매수/과매도 판정."""
    period = 14
    if len(prices) < period + 1:
        raise ValueError(f"RSI 계산을 위해 최소 {period + 1}일치 데이터가 필요합니다.")

    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    gains  = [d for d in deltas[-period:] if d > 0]
    losses = [-d for d in deltas[-period:] if d < 0]

    avg_gain = sum(gains) / period if gains else 0.0
    avg_loss = sum(losses) / period if losses else 0.0

    if avg_loss == 0:
        rsi = 100.0
    else:
        rs  = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

    if rsi <= 30:
        signal = SignalType.BUY
    elif rsi >= 70:
        signal = SignalType.SELL
    else:
        signal = SignalType.HOLD

    reason = f"RSI({period})={rsi:.1f} → {signal.value}"
    return signal, reason


def _calc_bollinger_signal(prices: list[float]) -> tuple[SignalType, str]:
    """볼린저밴드 20일 기준 상·하단 돌파 판정."""
    period = 20
    if len(prices) < period:
        raise ValueError(f"볼린저밴드 계산을 위해 최소 {period}일치 데이터가 필요합니다.")

    window = prices[-period:]
    ma     = sum(window) / period
    std    = (sum((p - ma) ** 2 for p in window) / period) ** 0.5
    upper  = ma + 2 * std
    lower  = ma - 2 * std
    close  = prices[-1]

    if close < lower:
        signal = SignalType.BUY
    elif close > upper:
        signal = SignalType.SELL
    else:
        signal = SignalType.HOLD

    reason = f"종가={close:,.0f} / 상단={upper:,.0f} / 하단={lower:,.0f} → {signal.value}"
    return signal, reason


# 전략 ID → 계산 함수 매핑 (분기문 없이 자동 연결)
_SIGNAL_CALCULATORS: dict[StrategyId, Callable] = {
    StrategyId.GOLDEN_CROSS: _calc_golden_cross_signal,
    StrategyId.RSI:          _calc_rsi_signal,
    StrategyId.BOLLINGER:    _calc_bollinger_signal,
}


# ------------------------------------------------------------------ #
# Repository
# ------------------------------------------------------------------ #

class InMemoryStrategyRepository:
    def __init__(self, market_data_repo: MarketDataRepository) -> None:
        self._market_data_repo = market_data_repo
        self._store: dict[str, Strategy] = {s.id: s for s in _DEFAULT_STRATEGIES}

    async def list(self) -> list[Strategy]:
        return list(self._store.values())

    async def get(self, strategy_id: StrategyId) -> Strategy:
        strategy = self._store.get(strategy_id)
        if strategy is None:
            raise StrategyNotFoundError(strategy_id)
        return strategy

    async def save(self, strategy: Strategy) -> Strategy:
        self._store[strategy.id] = strategy
        return strategy

    async def generate_signal(self, strategy_id: StrategyId, stock_code: str) -> Signal:
        await self.get(strategy_id)  # 존재 여부 확인

        candles = await self._market_data_repo.get_candles(
            stock_code, period=CandlePeriod.THREE_MONTHS, count=30
        )
        prices = [float(c.close) for c in candles]

        calc = _SIGNAL_CALCULATORS[strategy_id]
        signal_type, reason = calc(prices)

        return Signal(
            strategy_id=strategy_id,
            stock_code=stock_code,
            signal_type=signal_type,
            generated_at=datetime.now(tz=timezone.utc).isoformat(),
            reason=reason,
        )
