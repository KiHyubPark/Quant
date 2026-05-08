import asyncio
import math
from concurrent.futures import ThreadPoolExecutor

import yfinance as yf

from app.domain.market_data.entity import Candle, Stock, Ticker
from app.domain.market_data.exceptions import StockNotFoundError

_executor = ThreadPoolExecutor(max_workers=4)

# 한국 거래소 exchange 코드 → 시장 구분
_EXCHANGE_TO_MARKET: dict[str, str] = {
    "KSC": "KOSPI",
    "KOQ": "KOSDAQ",
}

# yfinance 종목 코드 suffix: KOSPI → .KS, KOSDAQ → .KQ
_SUFFIXES = (".KS", ".KQ")


class YFinanceMarketDataRepository:
    """yfinance 기반 시장 데이터 조회 (국내 주식)"""

    # ------------------------------------------------------------------ #
    # 내부 헬퍼                                                            #
    # ------------------------------------------------------------------ #

    def _resolve_ticker(self, code: str) -> yf.Ticker:
        """종목 코드(6자리)로 유효한 Ticker를 찾아 반환."""
        for suffix in _SUFFIXES:
            ticker = yf.Ticker(f"{code}{suffix}")
            price = ticker.fast_info.last_price
            if price is not None and not math.isnan(price) and price > 0:
                return ticker
        raise StockNotFoundError(code)

    # ------------------------------------------------------------------ #
    # 공개 메서드 (비동기 — 동기 yfinance 호출을 ThreadPoolExecutor 위임)  #
    # ------------------------------------------------------------------ #

    async def search_stocks(self, keyword: str) -> list[Stock]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._sync_search_stocks, keyword)

    def _sync_search_stocks(self, keyword: str) -> list[Stock]:
        results = yf.Search(keyword, news_count=0).quotes
        stocks: list[Stock] = []
        for item in results:
            symbol: str = item.get("symbol", "")
            if not symbol.endswith((".KS", ".KQ")):
                continue
            code = symbol.rsplit(".", 1)[0]
            exchange = item.get("exchange", "")
            market = _EXCHANGE_TO_MARKET.get(exchange, exchange)
            name = item.get("shortname") or item.get("longname") or code
            stocks.append(Stock(code=code, name=name, market=market))
        return stocks

    async def get_candles(self, code: str, period: str, count: int) -> list[Candle]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._sync_get_candles, code, period, count)

    def _sync_get_candles(self, code: str, period: str, count: int) -> list[Candle]:
        ticker = self._resolve_ticker(code)
        hist = ticker.history(period=period)
        if hist.empty:
            raise StockNotFoundError(code)

        candles: list[Candle] = []
        for date, row in hist.iterrows():
            candles.append(
                Candle(
                    date=date.strftime("%Y%m%d"),
                    open=int(row["Open"]),
                    high=int(row["High"]),
                    low=int(row["Low"]),
                    close=int(row["Close"]),
                    volume=int(row["Volume"]),
                )
            )

        return candles[-count:]

    async def get_ticker(self, code: str) -> Ticker:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._sync_get_ticker, code)

    def _sync_get_ticker(self, code: str) -> Ticker:
        ticker = self._resolve_ticker(code)
        info = ticker.fast_info

        price = int(info.last_price or 0)
        prev_close = int(info.previous_close or price)
        change = price - prev_close
        change_rate = round(change / prev_close * 100, 2) if prev_close else 0.0

        return Ticker(code=code, price=price, change=change, change_rate=change_rate)
