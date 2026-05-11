from app.domain.strategy.entity import SignalType


def calculate(prices: list[float]) -> tuple[SignalType, str]:
    """RSI 14일 기준 과매수/과매도 판정.

    - RSI <= 30 → BUY  (과매도)
    - RSI >= 70 → SELL (과매수)
    - 그 외     → HOLD
    """
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
