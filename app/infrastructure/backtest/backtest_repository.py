import asyncio
import math
import uuid
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import yfinance as yf

from app.domain.backtest.entity import BacktestResult, PerformanceMetrics
from app.domain.backtest.exceptions import BacktestResultNotFoundError

_executor = ThreadPoolExecutor(max_workers=2)

# 연간 거래일 수 (샤프 지수 연환산 기준)
_TRADING_DAYS_PER_YEAR = 252
# 무위험 수익률 (연 3.5% 기준, 일간 환산)
_RISK_FREE_DAILY = 0.035 / _TRADING_DAYS_PER_YEAR


def _sync_run_backtest(
    stock_code: str,
    start_date: str,
    end_date: str,
    initial_capital: int,
) -> dict:
    """
    yfinance로 OHLCV 데이터를 로드하고
    MA5/MA20 골든크로스 전략으로 백테스트를 실행한다.

    반환값: dict (BacktestResult 생성에 필요한 원시 데이터)
    """
    ticker_code = f"{stock_code}.KS"
    start = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
    end = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"

    df: pd.DataFrame = yf.download(ticker_code, start=start, end=end, progress=False)

    if df.empty:
        # KOSDAQ 재시도
        ticker_code = f"{stock_code}.KQ"
        df = yf.download(ticker_code, start=start, end=end, progress=False)

    if df.empty:
        raise ValueError(f"데이터를 불러올 수 없습니다. (code={stock_code})")

    # Close 컬럼이 MultiIndex인 경우 단일 컬럼으로 변환
    close: pd.Series = df["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    close = close.dropna()

    # MA5 / MA20 계산
    ma5 = close.rolling(5).mean()
    ma20 = close.rolling(20).mean()

    # 시그널 생성: 골든크로스 → BUY, 데드크로스 → SELL
    # (NaN을 제거하기 위해 dropna 이후의 인덱스 기준)
    valid = pd.DataFrame({"close": close, "ma5": ma5, "ma20": ma20}).dropna()

    signals = pd.Series(0, index=valid.index)  # 0=HOLD, 1=BUY, -1=SELL
    prev_above = (valid["ma5"].iloc[0] > valid["ma20"].iloc[0])
    for i in range(1, len(valid)):
        curr_above = valid["ma5"].iloc[i] > valid["ma20"].iloc[i]
        if curr_above and not prev_above:
            signals.iloc[i] = 1   # 골든크로스
        elif not curr_above and prev_above:
            signals.iloc[i] = -1  # 데드크로스
        prev_above = curr_above

    # 포지션 시뮬레이션
    cash = float(initial_capital)
    shares = 0
    buy_price = 0.0
    trades: list[dict] = []

    for i, (date, row) in enumerate(valid.iterrows()):
        price = float(row["close"])
        sig = signals.iloc[i]

        if sig == 1 and shares == 0:
            shares = int(cash // price)
            if shares > 0:
                buy_price = price
                cash -= shares * price
                trades.append({"type": "BUY", "price": price, "shares": shares})

        elif sig == -1 and shares > 0:
            sell_value = shares * price
            profit = sell_value - shares * buy_price
            trades.append({"type": "SELL", "price": price, "shares": shares, "profit": profit})
            cash += sell_value
            shares = 0
            buy_price = 0.0

    # 미체결 포지션은 마지막 날 가격으로 청산
    if shares > 0:
        last_price = float(valid["close"].iloc[-1])
        profit = shares * last_price - shares * buy_price
        trades.append({"type": "SELL", "price": last_price, "shares": shares, "profit": profit})
        cash += shares * last_price
        shares = 0

    final_capital = int(cash)

    # PerformanceMetrics 계산
    total_return = (final_capital - initial_capital) / initial_capital * 100

    # 연환산 수익률 (CAGR)
    days = (valid.index[-1] - valid.index[0]).days if len(valid) > 1 else 1
    years = days / 365.0
    annualized_return = ((final_capital / initial_capital) ** (1 / max(years, 1e-6)) - 1) * 100 if years > 0 else 0.0

    # 최대 낙폭 (MDD)
    daily_returns = valid["close"].pct_change().dropna()
    cumulative = (1 + daily_returns).cumprod()
    peak = cumulative.cummax()
    drawdown = (cumulative - peak) / peak
    max_drawdown = float(drawdown.min() * 100)

    # 샤프 지수
    excess = daily_returns - _RISK_FREE_DAILY
    std = excess.std()
    sharpe_ratio = float((excess.mean() / std * math.sqrt(_TRADING_DAYS_PER_YEAR)) if std > 0 else 0.0)

    # 승률
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
    """
    yfinance + pandas 기반 백테스트 저장소.
    결과는 인메모리 캐시에 저장된다.
    """

    def __init__(self) -> None:
        self._cache: dict[str, BacktestResult] = {}

    async def run(
        self,
        strategy_id: str,
        stock_code: str,
        start_date: str,
        end_date: str,
        initial_capital: int,
    ) -> BacktestResult:
        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(
            _executor,
            _sync_run_backtest,
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
