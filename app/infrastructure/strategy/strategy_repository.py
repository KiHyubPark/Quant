from datetime import datetime, timezone

from app.domain.market_data.repository import MarketDataRepository
from app.domain.strategy.entity import Signal, SignalType, Strategy
from app.domain.strategy.exceptions import StrategyNotFoundError

# 기본 제공 전략
_DEFAULT_STRATEGIES: list[Strategy] = [
    Strategy(
        id="golden-cross",
        name="골든크로스",
        description="MA5가 MA20을 상향 돌파하면 BUY, 하향 돌파하면 SELL",
    ),
]


def _moving_average(prices: list[float], period: int) -> float:
    if len(prices) < period:
        raise ValueError(f"가격 데이터가 부족합니다. (필요: {period}, 현재: {len(prices)})")
    return sum(prices[-period:]) / period


def _calc_golden_cross_signal(prices: list[float]) -> SignalType:
    """
    MA5 / MA20 골든크로스·데드크로스 판정.

    - 오늘 MA5 > MA20, 어제 MA5 <= MA20 → 골든크로스 → BUY
    - 오늘 MA5 < MA20, 어제 MA5 >= MA20 → 데드크로스 → SELL
    - 그 외 → HOLD
    """
    if len(prices) < 21:
        raise ValueError("MA20 계산을 위해 최소 21일치 데이터가 필요합니다.")

    today_ma5 = _moving_average(prices, 5)
    today_ma20 = _moving_average(prices, 20)

    yesterday_ma5 = _moving_average(prices[:-1], 5)
    yesterday_ma20 = _moving_average(prices[:-1], 20)

    if today_ma5 > today_ma20 and yesterday_ma5 <= yesterday_ma20:
        return SignalType.BUY
    if today_ma5 < today_ma20 and yesterday_ma5 >= yesterday_ma20:
        return SignalType.SELL
    return SignalType.HOLD


class InMemoryStrategyRepository:
    """
    인메모리 전략 저장소.

    generate_signal은 MarketDataRepository로 캔들을 조회하여
    MA5/MA20 골든크로스 기반 시그널을 계산한다.
    """

    def __init__(self, market_data_repo: MarketDataRepository) -> None:
        self._market_data_repo = market_data_repo
        self._store: dict[str, Strategy] = {s.id: s for s in _DEFAULT_STRATEGIES}

    async def list(self) -> list[Strategy]:
        return list(self._store.values())

    async def get(self, strategy_id: str) -> Strategy:
        strategy = self._store.get(strategy_id)
        if strategy is None:
            raise StrategyNotFoundError(strategy_id)
        return strategy

    async def save(self, strategy: Strategy) -> Strategy:
        self._store[strategy.id] = strategy
        return strategy

    async def generate_signal(self, strategy_id: str, stock_code: str) -> Signal:
        strategy = await self.get(strategy_id)

        # MA20 + 여유분 30일치 캔들 조회
        candles = await self._market_data_repo.get_candles(stock_code, period="3mo", count=30)

        prices = [float(c.close) for c in candles]
        signal_type = _calc_golden_cross_signal(prices)

        today_ma5 = _moving_average(prices, 5)
        today_ma20 = _moving_average(prices, 20)
        reason = (
            f"MA5={today_ma5:,.0f} / MA20={today_ma20:,.0f} → {signal_type.value}"
        )

        return Signal(
            strategy_id=strategy.id,
            stock_code=stock_code,
            signal_type=signal_type,
            generated_at=datetime.now(tz=timezone.utc).isoformat(),
            reason=reason,
        )
