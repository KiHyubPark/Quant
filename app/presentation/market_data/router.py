from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, Query

from app.application.market_data.commands import GetCandlesCommand, GetTickerCommand, SearchStocksCommand
from app.application.market_data.use_cases import MarketDataUseCases
from app.domain.market_data.exceptions import StockNotFoundError
from app.infrastructure.market_data.market_data_repository import YFinanceMarketDataRepository
from app.presentation.market_data.schemas import CandleSchema, StockSchema, TickerSchema

router = APIRouter(prefix="/market-data", tags=["Market Data"])


def get_use_cases() -> MarketDataUseCases:
    return MarketDataUseCases(YFinanceMarketDataRepository())


@router.get("/stocks/search", response_model=list[StockSchema], summary="종목 검색")
async def search_stocks(
    keyword: str = Query(..., description="종목명 또는 종목 코드"),
    use_cases: MarketDataUseCases = Depends(get_use_cases),
):
    stocks = await use_cases.search_stocks(SearchStocksCommand(keyword=keyword))
    return [asdict(s) for s in stocks]


@router.get("/stocks/{code}/candles", response_model=list[CandleSchema], summary="캔들(OHLCV) 조회")
async def get_candles(
    code: str,
    period: str = Query("3mo", description="조회 기간 (1d / 5d / 1mo / 3mo / 6mo / 1y / 2y / 5y)"),
    count: int = Query(100, ge=1, le=1000, description="최대 캔들 수"),
    use_cases: MarketDataUseCases = Depends(get_use_cases),
):
    try:
        candles = await use_cases.get_candles(GetCandlesCommand(code=code, period=period, count=count))
        return [asdict(c) for c in candles]
    except StockNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/stocks/{code}/ticker", response_model=TickerSchema, summary="현재가 조회")
async def get_ticker(
    code: str,
    use_cases: MarketDataUseCases = Depends(get_use_cases),
):
    try:
        ticker = await use_cases.get_ticker(GetTickerCommand(code=code))
        return asdict(ticker)
    except StockNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
