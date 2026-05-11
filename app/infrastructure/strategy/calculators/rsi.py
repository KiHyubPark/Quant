from app.domain.market_data.entity import Candle
from app.domain.strategy.entity import SignalType


def calculate(candles: list[Candle]) -> tuple[SignalType, str]:
    """RSI 14일 기준 과매수/과매도 판정 (Wilder's Smoothing).

    - RSI <= 30 → BUY  (과매도)
    - RSI >= 70 → SELL (과매수)
    - 그 외     → HOLD

    Wilder's Smoothing: 첫 avg는 단순 평균, 이후 EMA 방식으로 누적
    avg = (prev_avg * (period - 1) + current) / period
    """
    period = 14
    if len(candles) < period + 1:
        raise ValueError(f"RSI 계산을 위해 최소 {period + 1}일치 데이터가 필요합니다.")

    prices = [float(c.close) for c in candles]
    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]

    # 초기 avg: 첫 period개 변화값의 단순 평균
    avg_gain = sum(d for d in deltas[:period] if d > 0) / period
    avg_loss = sum(-d for d in deltas[:period] if d < 0) / period

    # Wilder's EMA: period+1 이후의 변화값 누적
    for delta in deltas[period:]:
        gain = delta if delta > 0 else 0.0
        loss = -delta if delta < 0 else 0.0
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

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
