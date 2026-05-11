import asyncio
import math
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

import pandas as pd
from pykrx import stock as krx

from app.domain.backtest.entity import BacktestResult, PerformanceMetrics
from app.domain.backtest.exceptions import BacktestResultNotFoundError
from app.domain.strategy.entity import SignalType, StrategyId
from app.infrastructure.strategy.calculators import bollinger, golden_cross, rsi

_executor = ThreadPoolExecutor(max_workers=2)

_TRADING_DAYS_PER_YEAR = 252
_RISK_FREE_DAILY = 0.035 / _TRADING_DAYS_PER_YEAR

# 전략 ID → 계산 함수 매핑
_SIGNAL_CALCULATORS: dict[StrategyId, Callable] = {
    StrategyId.GOLDEN_CROSS: golden_cross.calculate,
    StrategyId.RSI:          rsi.calculate,
    StrategyId.BOLLINGER:    bollinger.calculate,
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

    prices = close.tolist()
    calc = _SIGNAL_CALCULATORS[strategy_id]

    # 날마다 해당 전략의 calculate() 호출로 시그널 생성
    signals: list[SignalType] = []
    for i in range(len(prices)):
        try:
            signal, _ = calc(prices[: i + 1])
        except ValueError:
            signal = SignalType.HOLD
        signals.append(signal)

    # 매매 시뮬레이션
    cash = float(initial_capital)
    shares = 0
    buy_price = 0.0
    trades: list[dict] = []

    for i, price in enumerate(prices):
        sig = signals[i]

        if sig == SignalType.BUY and shares == 0:
            shares = int(cash // price)
            if shares > 0:
                buy_price = price
                cash -= shares * price
                trades.append({"type": "BUY", "price": price, "shares": shares})

        elif sig == SignalType.SELL and shares > 0:
            sell_value = shares * price
            profit = sell_value - shares * buy_price
            trades.append({"type": "SELL", "price": price, "shares": shares, "profit": profit})
            cash += sell_value
            shares = 0
            buy_price = 0.0

    # 기간 종료 시 보유 중이면 강제 매도
    if shares > 0:
        last_price = prices[-1]
        profit = shares * last_price - shares * buy_price
        trades.append({"type": "SELL", "price": last_price, "shares": shares, "profit": profit})
        cash += shares * last_price

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
        loop = asyncio.get_event_loop()
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
