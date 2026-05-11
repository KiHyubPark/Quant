from app.domain.market_data.entity import Candle
from app.domain.strategy.entity import SignalType


def _moving_average(prices: list[float], period: int) -> float:
    if len(prices) < period:
        raise ValueError(f"가격 데이터가 부족합니다. (필요: {period}, 현재: {len(prices)})")
    return sum(prices[-period:]) / period


def calculate(candles: list[Candle]) -> tuple[SignalType, str]:
    """MA5 / MA20 골든크로스·데드크로스 판정.

    - 오늘 MA5 > MA20, 어제 MA5 <= MA20 → 골든크로스 → BUY
    - 오늘 MA5 < MA20, 어제 MA5 >= MA20 → 데드크로스 → SELL
    - 그 외 → HOLD
    """
    if len(candles) < 21:
        raise ValueError("MA20 계산을 위해 최소 21일치 데이터가 필요합니다.")

    prices = [float(c.close) for c in candles]

    today_ma5      = _moving_average(prices, 5)
    today_ma20     = _moving_average(prices, 20)
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
