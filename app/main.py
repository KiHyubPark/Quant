import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.presentation.backtest import router as backtest
from app.presentation.booking import router as booking
from app.presentation.market_data import router as market_data
from app.presentation.order import router as order
from app.presentation.portfolio import router as portfolio
from app.presentation.strategy import router as strategy
from app.scheduler.trading_job import create_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = create_scheduler()
    scheduler.start()
    logging.getLogger(__name__).info("자동매매 스케줄러 시작 (jobs=%d)", len(scheduler.get_jobs()))
    yield
    scheduler.shutdown()
    logging.getLogger(__name__).info("자동매매 스케줄러 종료")


app = FastAPI(
    title="Quant",
    description="주식 자동매매 / 퀀트 투자 시스템",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(booking.router)
app.include_router(market_data.router)
app.include_router(strategy.router)
app.include_router(order.router)
app.include_router(portfolio.router)
app.include_router(backtest.router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
