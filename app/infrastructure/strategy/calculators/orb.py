from app.domain.market_data.entity import Candle
from app.domain.strategy.entity import SignalType

# SSRN 2024 논문 기준 — 거래량 2배 이상일 때 돌파의 유의미성 검증됨
_VOLUME_LOOKBACK   = 20
_VOLUME_MULTIPLIER = 2.0


def calculate(candles: list[Candle]) -> tuple[SignalType, str]:
    """Opening Range Breakout (ORB) 일봉 적용 버전.

    - 오늘 종가 > 전일 고가  AND  오늘 거래량 > 20일 평균 × 2  → BUY
    - 오늘 종가 < 전일 저가  AND  오늘 거래량 > 20일 평균 × 2  → SELL
    - 그 외                                                     → HOLD

    추세 돌파 + 거래량 동반 확인으로 가짜 돌파를 걸러낸다.
    """
    if len(candles) < _VOLUME_LOOKBACK + 1:
        raise ValueError(
            f"ORB 계산을 위해 최소 {_VOLUME_LOOKBACK + 1}일치 데이터가 필요합니다."
        )

    today      = candles[-1]
    yesterday  = candles[-2]
    recent_vol = [c.volume for c in candles[-(_VOLUME_LOOKBACK + 1):-1]]
    avg_volume = sum(recent_vol) / len(recent_vol)
    rvol       = today.volume / avg_volume if avg_volume > 0 else 0.0

    high_breakout = today.close > yesterday.high
    low_breakout  = today.close < yesterday.low
    volume_surge  = rvol > _VOLUME_MULTIPLIER

    if high_breakout and volume_surge:
        signal = SignalType.BUY
    elif low_breakout and volume_surge:
        signal = SignalType.SELL
    else:
        signal = SignalType.HOLD

    reason = (
        f"종가={today.close:,.0f} / 전일고가={yesterday.high:,.0f} / "
        f"RVOL={rvol:.2f}배 → {signal.value}"
    )
    return signal, reason
