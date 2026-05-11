import asyncio
import math
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

import pandas as pd
from pykrx import stock as krx

from app.domain.backtest.entity import BacktestResult, PerformanceMetrics
from app.domain.backtest.exceptions import BacktestResultNotFoundError
from app.domain.market_data.entity import Candle
from app.domain.strategy.entity import SignalType, StrategyId
from app.infrastructure.strategy.calculators import bollinger, golden_cross, orb, rsi

_executor = ThreadPoolExecutor(max_workers=2)

_TRADING_DAYS_PER_YEAR = 252
_RISK_FREE_DAILY = 0.035 / _TRADING_DAYS_PER_YEAR

# 거래비용 — 매수/매도 1회당 비율
# KOSPI 기준: 위탁수수료 0.015% + 거래세 0.20% (코스닥 0.18%) ≈ 매도시 0.215%
# 보수적으로 매수 0.05%, 매도 0.25% 적용 → 왕복 약 0.3%
_BUY_COST_RATE  = 0.0005
_SELL_COST_RATE = 0.0025

# 전략 ID → 계산 함수 매핑
_SIGNAL_CALCULATORS: dict[StrategyId, Callable] = {
    StrategyId.GOLDEN_CROSS: golden_cross.calculate,
    StrategyId.RSI:          rsi.calculate,
    StrategyId.BOLLINGER:    bollinger.calculate,
    StrategyId.ORB:          orb.calculate,
}

# 전략별 강제 보유 기간 (일)
# 0  → SELL 시그널이 나올 때까지 보유 (추세 추종형)
# 1+ → 매수 후 N일 뒤 종가에 무조건 매도 (단타형)
_HOLD_DAYS: dict[StrategyId, int] = {
    StrategyId.ORB: 1,  # ORB는 단타 전략 — 다음날 종가 매도
}


def _sync_run_backtest(
    strategy_id: StrategyId,
    stock_code: str,
    start_date: str,
    end_date: str,
    initial_capital: int,
) -> dict:
    df: pd.DataFrame = krx.get_market_ohlcv(start_date, end_date, stock_code)

    if df is None or df.empty:
        raise ValueError(f"데이터를 불러올 수 없습니다. (code={stock_code})")

    close: pd.Series = df["종가"].astype(float).dropna()

    if len(close) < 20:
        raise ValueError(f"백테스트에 필요한 최소 데이터(20일)가 부족합니다. (code={stock_code})")

    # OHLCV → Candle 리스트로 변환 (calculator 인터페이스 통일)
    candles: list[Candle] = [
        Candle(
            date=dt.strftime("%Y%m%d"),
            open=int(row["시가"]),
            high=int(row["고가"]),
            low=int(row["저가"]),
            close=int(row["종가"]),
            volume=int(row["거래량"]),
        )
        for dt, row in df.iterrows()
    ]
    prices = [float(c.close) for c in candles]
    calc = _SIGNAL_CALCULATORS[strategy_id]

    # 날마다 해당 전략의 calculate() 호출로 시그널 생성
    signals: list[SignalType] = []
    for i in range(len(candles)):
        try:
            signal, _ = calc(candles[: i + 1])
        except ValueError:
            signal = SignalType.HOLD
        signals.append(signal)

    # 매매 시뮬레이션
    # 핵심: 시그널은 i일 종가에 발생 → 실제 체결은 i+1일에 일어남 (look-ahead bias 제거)
    #   - 매수: i+1일 시가
    #   - 추세 추종 매도: i+1일 시가
    #   - 단타 강제 매도: 매수한 그 날(i+1)의 종가
    cash = float(initial_capital)
    shares = 0
    buy_price = 0.0
    hold_count = 0  # 강제 매도까지 남은 일수 (0 = 비활성)
    trades: list[dict] = []
    forced_hold_days = _HOLD_DAYS.get(strategy_id, 0)

    for i in range(len(candles) - 1):
        sig = signals[i]
        exec_candle = candles[i + 1]  # 시그널 다음 봉에서 실제 체결

        # 단타 전략: 보유 카운트 감소 후 0이 되는 날의 종가에 매도
        if shares > 0 and hold_count > 0:
            hold_count -= 1
            if hold_count == 0:
                sell_at = float(exec_candle.close)
                gross   = shares * sell_at
                net     = gross * (1 - _SELL_COST_RATE)
                profit  = net - shares * buy_price
                trades.append({"type": "SELL", "price": sell_at, "shares": shares, "profit": profit})
                cash += net
                shares = 0
                buy_price = 0.0
                continue

        # 매수 (다음날 시가)
        if sig == SignalType.BUY and shares == 0:
            buy_at  = float(exec_candle.open)
            qty     = int(cash // (buy_at * (1 + _BUY_COST_RATE)))
            if qty > 0:
                cost = qty * buy_at * (1 + _BUY_COST_RATE)
                shares = qty
                buy_price = buy_at * (1 + _BUY_COST_RATE)  # 매수단가에 수수료 반영
                cash -= cost
                trades.append({"type": "BUY", "price": buy_at, "shares": qty})
                hold_count = forced_hold_days  # 단타 전략이면 카운트다운 시작

        # 추세 추종 매도 (다음날 시가)
        elif sig == SignalType.SELL and shares > 0 and forced_hold_days == 0:
            sell_at = float(exec_candle.open)
            gross   = shares * sell_at
            net     = gross * (1 - _SELL_COST_RATE)
            profit  = net - shares * buy_price
            trades.append({"type": "SELL", "price": sell_at, "shares": shares, "profit": profit})
            cash += net
            shares = 0
            buy_price = 0.0

    # 기간 종료 시 보유 중이면 마지막 종가로 강제 매도
    if shares > 0:
        last_price = float(candles[-1].close)
        gross  = shares * last_price
        net    = gross * (1 - _SELL_COST_RATE)
        profit = net - shares * buy_price
        trades.append({"type": "SELL", "price": last_price, "shares": shares, "profit": profit})
        cash += net

    final_capital = int(cash)
    total_return = (final_capital - initial_capital) / initial_capital * 100

    days = (close.index[-1] - close.index[0]).days if len(close) > 1 else 1
    years = days / 365.0
    annualized_return = (
        ((final_capital / initial_capital) ** (1 / max(years, 1e-6)) - 1) * 100
        if years > 0 else 0.0
    )

    daily_returns = close.pct_change().dropna()
    cumulative = (1 + daily_returns).cumprod()
    peak = cumulative.cummax()
    max_drawdown = float(((cumulative - peak) / peak).min() * 100)

    excess = daily_returns - _RISK_FREE_DAILY
    std = excess.std()
    sharpe_ratio = float(
        (excess.mean() / std * math.sqrt(_TRADING_DAYS_PER_YEAR)) if std > 0 else 0.0
    )

    sell_trades = [t for t in trades if t["type"] == "SELL"]
    total_trades = len(sell_trades)
    win_trades = sum(1 for t in sell_trades if t.get("profit", 0) > 0)
    win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0.0

    return {
        "final_capital": final_capital,
        "metrics": PerformanceMetrics(
            total_return=round(total_return, 2),
            annualized_return=round(annualized_return, 2),
            max_drawdown=round(max_drawdown, 2),
            sharpe_ratio=round(sharpe_ratio, 4),
            win_rate=round(win_rate, 2),
            total_trades=total_trades,
        ),
    }


class PandasBacktestRepository:
    def __init__(self) -> None:
        self._cache: dict[str, BacktestResult] = {}

    async def run(
        self,
        strategy_id: StrategyId,
        stock_code: str,
        start_date: str,
        end_date: str,
        initial_capital: int,
    ) -> BacktestResult:
        loop = asyncio.get_running_loop()
        raw = await loop.run_in_executor(
            _executor,
            _sync_run_backtest,
            strategy_id,
            stock_code,
            start_date,
            end_date,
            initial_capital,
        )

        result = BacktestResult(
            result_id=str(uuid.uuid4()),
            strategy_id=strategy_id,
            stock_code=stock_code,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            final_capital=raw["final_capital"],
            metrics=raw["metrics"],
        )
        self._cache[result.result_id] = result
        return result

    async def get(self, result_id: str) -> BacktestResult:
        result = self._cache.get(result_id)
        if result is None:
            raise BacktestResultNotFoundError(result_id)
        return result
