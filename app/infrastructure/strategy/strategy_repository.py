from datetime import datetime, timezone
from typing import Callable

from app.domain.market_data.entity import CandlePeriod
from app.domain.market_data.repository import MarketDataRepository
from app.domain.strategy.entity import Signal, SignalType, Strategy, StrategyId
from app.domain.strategy.exceptions import StrategyNotFoundError
from app.infrastructure.strategy.calculators import bollinger, golden_cross, rsi

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

# 전략 ID → 계산 함수 매핑
_SIGNAL_CALCULATORS: dict[StrategyId, Callable] = {
    StrategyId.GOLDEN_CROSS: golden_cross.calculate,
    StrategyId.RSI:          rsi.calculate,
    StrategyId.BOLLINGER:    bollinger.calculate,
}


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
