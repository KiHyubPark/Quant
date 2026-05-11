---
name: backtest-bias-check
description: 백테스트 코드의 Look-ahead Bias(선행편향) 탐지 및 수정 가이드
version: 1.0.0
---

# Backtest Look-ahead Bias 체크

백테스트에서 Look-ahead Bias(선행편향)는 시그널 생성 시점에 실제로 알 수 없는 미래 데이터를 사용해 성과를 과대 평가하는 문제다. 아래 체크리스트와 패턴을 기준으로 코드를 검토한다.

## 핵심 원칙

**시그널 발생 시점과 체결 시점은 반드시 분리되어야 한다.**

| 시점 | 허용 데이터 |
|------|------------|
| i일 시그널 계산 | `candles[:i+1]` (i일 종가까지) |
| 체결 (매수/매도) | `candles[i+1]` (i+1일 데이터) |
| 당일 매수·당일 종가 매도 | `candles[i+1].open` 매수 → `candles[i+1].close` 매도 허용 |

---

## 체크리스트

### 1. 시그널 계산

```python
# ✅ GOOD: 현재 인덱스까지의 데이터만 사용
signal = calc(candles[:i + 1])

# ❌ BAD: 미래 데이터 포함
signal = calc(candles)           # 전체 데이터 사용
signal = calc(candles[:i + 2])  # i+1일 데이터 사용
```

- [ ] `calc()` 또는 지표 계산 함수가 슬라이싱(`[:i+1]`)으로 호출되는가?
- [ ] 지표 함수 내부에서 전역 배열 전체를 참조하지 않는가?

### 2. 체결 가격

```python
exec_candle = candles[i + 1]  # 반드시 다음 봉 사용

# ✅ GOOD
buy_at = float(exec_candle.open)   # 다음날 시가 매수
sell_at = float(exec_candle.open)  # 다음날 시가 매도 (추세 추종)
sell_at = float(exec_candle.close) # 다음날 종가 매도 (단타 — 허용)

# ❌ BAD
buy_at = float(candles[i].close)   # 시그널 발생 당일 종가 체결 (look-ahead)
buy_at = float(candles[i].open)    # 시그널 발생 당일 시가 체결 (look-ahead)
```

- [ ] 매수/매도 체결 가격이 `candles[i+1]`에서 가져오는가?
- [ ] 시그널 발생일(`candles[i]`)의 가격으로 체결하지 않는가?

### 3. 루프 범위

```python
# ✅ GOOD: 마지막 봉은 체결 불가이므로 -1까지
for i in range(len(candles) - 1):
    sig = signals[i]
    exec_candle = candles[i + 1]

# ❌ BAD: 마지막 봉에서 i+1 인덱스 오류 또는 미래 데이터 참조
for i in range(len(candles)):
    exec_candle = candles[i + 1]  # IndexError 또는 패딩 시 bias
```

- [ ] 루프가 `range(len(candles) - 1)`인가?

### 4. 지표 함수 내부

각 지표 함수가 입력 배열(`candles` 또는 `prices`) 외부 데이터를 참조하지 않는지 확인한다.

**골든크로스 (MA5/MA20)**
```python
# ✅ GOOD: prices[-1]은 입력 배열의 마지막 원소 (= 현재 시점)
today_ma5  = sum(prices[-5:]) / 5
today_ma20 = sum(prices[-20:]) / 20
yesterday_ma5  = sum(prices[:-1][-5:]) / 5
yesterday_ma20 = sum(prices[:-1][-20:]) / 20
```

**RSI**
```python
# ✅ GOOD: deltas[-period:]는 입력 데이터 내부만 참조
deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
gains  = [d for d in deltas[-period:] if d > 0]
```

> **주의 — RSI 정확도**: 표준 RSI는 Wilder's Smoothing(EMA 방식)을 사용한다.
> 단순 평균은 bias는 아니지만 실제 지표와 수치가 달라 신호 발생 빈도가 다를 수 있다.
>
> Wilder's Smoothing 구현:
> ```python
> # 첫 avg_gain/avg_loss는 단순 평균, 이후 EMA
> avg_gain = sum(gains[:period]) / period
> for g in gains[period:]:
>     avg_gain = (avg_gain * (period - 1) + g) / period
> ```

**볼린저밴드**
```python
# ✅ GOOD: prices[-period:]는 현재 시점 이전 window
window = prices[-period:]
ma    = sum(window) / period
std   = (sum((p - ma) ** 2 for p in window) / period) ** 0.5
```

### 5. 종료 시 강제 매도

```python
# ✅ GOOD: 기간 종료 후 마지막 봉 종가 — 실제 운용에서도 가능한 청산 가격
if shares > 0:
    last_price = float(candles[-1].close)
```

기간 종료 후 청산은 bias가 아니다. 단, 청산이 없을 경우 미실현 수익을 어떻게 계산하는지 명확히 해야 한다.

---

## 이 프로젝트의 현황

| 항목 | 상태 | 비고 |
|------|------|------|
| 시그널 계산 슬라이싱 | ✅ | `calc(candles[:i+1])` |
| 체결 가격 (다음날 시가) | ✅ | `exec_candle = candles[i+1]` |
| 루프 범위 | ✅ | `range(len(candles) - 1)` |
| ORB 단타 당일 종가 매도 | ✅ | 설계상 허용 |
| 기간 종료 청산 | ✅ | `candles[-1].close` |
| RSI Wilder's Smoothing | ⚠️ | 단순 평균 사용 — bias 아님, 정확도 이슈 |
| `asyncio.get_event_loop()` | ⚠️ | `backtest_repository.py:197` — deprecated |

---

## 수정 우선순위

1. **HIGH** — `asyncio.get_event_loop()` → `asyncio.get_running_loop()`
2. **MEDIUM** — RSI 단순 평균 → Wilder's Smoothing (신호 정확도 개선)

## 관련 파일

- `app/infrastructure/backtest/backtest_repository.py` — 시뮬레이션 루프
- `app/infrastructure/strategy/calculators/*.py` — 지표 계산 함수
