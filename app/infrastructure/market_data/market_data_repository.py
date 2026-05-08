import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from typing import Optional

from pykrx import stock as krx

from app.domain.market_data.entity import Candle, Stock, Ticker
from app.domain.market_data.exceptions import StockNotFoundError

_executor = ThreadPoolExecutor(max_workers=4)

_PERIOD_DAYS: dict[str, int] = {
    "1d": 1,
    "5d": 5,
    "1mo": 30,
    "3mo": 90,
    "6mo": 180,
    "1y": 365,
    "2y": 730,
    "5y": 1825,
}

# {code: (name, market)} 전체 종목 캐시 — 첫 search_stocks 호출 시 1회 로드
_stock_cache: Optional[dict[str, tuple[str, str]]] = None


def _recent_trading_date() -> str:
    """가장 최근 평일(거래일 근사치)을 YYYYMMDD 형식으로 반환."""
    d = date.today()
    for _ in range(7):
        if d.weekday() < 5:
            return d.strftime("%Y%m%d")
        d -= timedelta(days=1)
    return d.strftime("%Y%m%d")


def _load_stock_cache() -> dict[str, tuple[str, str]]:
    """KOSPI + KOSDAQ 전체 종목 코드/이름/시장을 한 번 로드해 캐싱."""
    global _stock_cache
    if _stock_cache is not None:
        return _stock_cache

    today = _recent_trading_date()
    cache: dict[str, tuple[str, str]] = {}
    for market in ("KOSPI", "KOSDAQ"):
        codes = krx.get_market_ticker_list(today, market=market)
        for code in codes:
            name = krx.get_market_ticker_name(code)
            cache[code] = (name, market)
    _stock_cache = cache
    return _stock_cache


class PykrxMarketDataRepository:
    """pykrx(KRX 공식 데이터) 기반 시장 데이터 조회 (국내 주식)"""

    # ------------------------------------------------------------------ #
    # 종목 검색                                                            #
    # ------------------------------------------------------------------ #

    async def search_stocks(self, keyword: str) -> list[Stock]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._sync_search_stocks, keyword)

    def _sync_search_stocks(self, keyword: str) -> list[Stock]:
        cache = _load_stock_cache()
        keyword_lower = keyword.lower()
        results: list[Stock] = []
        for code, (name, market) in cache.items():
            if keyword_lower in code.lower() or keyword_lower in name.lower():
                results.append(Stock(code=code, name=name, market=market))
        return results[:50]

    # ------------------------------------------------------------------ #
    # 캔들(OHLCV)                                                          #
    # ------------------------------------------------------------------ #

    async def get_candles(self, code: str, period: str, count: int) -> list[Candle]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._sync_get_candles, code, period, count)

    def _sync_get_candles(self, code: str, period: str, count: int) -> list[Candle]:
        days = _PERIOD_DAYS.get(period, 90)
        end = date.today()
        start = end - timedelta(days=days)

        df = krx.get_market_ohlcv(
            start.strftime("%Y%m%d"),
            end.strftime("%Y%m%d"),
            code,
        )

        if df is None or df.empty:
            raise StockNotFoundError(code)

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
        return candles[-count:]

    # ------------------------------------------------------------------ #
    # 현재가                                                               #
    # ------------------------------------------------------------------ #

    async def get_ticker(self, code: str) -> Ticker:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._sync_get_ticker, code)

    def _sync_get_ticker(self, code: str) -> Ticker:
        end = date.today()
        start = end - timedelta(days=7)

        # 현재가는 액면분할 수정 없는 실제 거래가를 사용
        df = krx.get_market_ohlcv(
            start.strftime("%Y%m%d"),
            end.strftime("%Y%m%d"),
            code,
            adjusted=False,
        )

        if df is None or df.empty:
            raise StockNotFoundError(code)

        price = int(df["종가"].iloc[-1])
        prev_close = int(df["종가"].iloc[-2]) if len(df) >= 2 else price
        change = price - prev_close
        change_rate = round(change / prev_close * 100, 2) if prev_close else 0.0

        return Ticker(code=code, price=price, change=change, change_rate=change_rate)
