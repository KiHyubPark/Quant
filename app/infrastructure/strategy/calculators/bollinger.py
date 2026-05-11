from app.domain.strategy.entity import SignalType


def calculate(prices: list[float]) -> tuple[SignalType, str]:
    """볼린저밴드 20일 기준 상·하단 돌파 판정.

    - 종가 < 하단 밴드(MA20 - 2σ) → BUY
    - 종가 > 상단 밴드(MA20 + 2σ) → SELL
    - 그 외                        → HOLD
    """
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
