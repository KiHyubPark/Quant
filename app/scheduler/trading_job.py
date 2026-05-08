"""
자동매매 스케줄러 (APScheduler 기반)

장 운영 시간 기준 작업 일정:
  09:05  — 등록된 전략별 매매 시그널 생성
  09:10  — BUY 시그널 → 시장가 주문 실행
  15:20  — SELL 시그널 → 시장가 주문 실행
  15:35  — 당일 체결 내역 로그 출력
"""

import logging
from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.application.order.commands import PlaceOrderCommand
from app.application.order.use_cases import OrderUseCases
from app.application.strategy.use_cases import StrategyUseCases
from app.domain.order.entity import OrderType
from app.domain.strategy.entity import SignalType
from app.infrastructure.market_data.market_data_repository import PykrxMarketDataRepository
from app.infrastructure.order.order_repository import InMemoryOrderRepository
from app.infrastructure.strategy.strategy_repository import InMemoryStrategyRepository

logger = logging.getLogger(__name__)

# 스케줄러가 사용할 싱글턴 repository
_market_data_repo = PykrxMarketDataRepository()
_strategy_repo = InMemoryStrategyRepository(market_data_repo=_market_data_repo)
_order_repo = InMemoryOrderRepository()

_strategy_use_cases = StrategyUseCases(_strategy_repo)
_order_use_cases = OrderUseCases(_order_repo)

# 자동매매 대상 종목 목록 (환경변수 또는 DB 연동 시 교체)
_WATCH_CODES: list[str] = ["005930", "000660"]  # 삼성전자, SK하이닉스


async def _generate_signals(session_type: str) -> dict[str, SignalType]:
    """등록된 모든 전략 × 종목 조합으로 시그널을 생성한다."""
    strategies = await _strategy_use_cases.list()
    signals: dict[str, SignalType] = {}

    for strategy in strategies:
        for code in _WATCH_CODES:
            try:
                signal = await _strategy_use_cases.generate_signal(strategy.id, code)
                signals[code] = signal.signal_type
                logger.info(
                    "[%s] 시그널 생성 — 전략=%s 종목=%s 시그널=%s 사유=%s",
                    session_type,
                    strategy.id,
                    code,
                    signal.signal_type.value,
                    signal.reason,
                )
            except Exception as exc:
                logger.warning("[%s] 시그널 생성 실패 — 종목=%s: %s", session_type, code, exc)

    return signals


async def job_morning_signal() -> None:
    """09:05 — 시그널 생성 (오전 장 시작 직후)"""
    logger.info("[장 시작] 시그널 생성 시작 (%s)", date.today())
    await _generate_signals("장 시작")


async def job_morning_buy() -> None:
    """09:10 — BUY 시그널이 있는 종목에 시장가 매수 주문"""
    logger.info("[장 시작] BUY 주문 실행 (%s)", date.today())
    signals = await _generate_signals("장 시작 매수")

    for code, signal_type in signals.items():
        if signal_type != SignalType.BUY:
            continue
        try:
            order = await _order_use_cases.place(
                PlaceOrderCommand(
                    stock_code=code,
                    order_type=OrderType.BUY,
                    quantity=1,   # 실운용 시 포지션 사이징 로직으로 교체
                    price=0,      # 시장가
                )
            )
            logger.info("[장 시작 매수] 주문 체결 — 종목=%s order_id=%s", code, order.order_id)
        except Exception as exc:
            logger.error("[장 시작 매수] 주문 실패 — 종목=%s: %s", code, exc)


async def job_close_sell() -> None:
    """15:20 — SELL 시그널이 있는 종목에 시장가 매도 주문"""
    logger.info("[장 마감] SELL 주문 실행 (%s)", date.today())
    signals = await _generate_signals("장 마감 매도")

    for code, signal_type in signals.items():
        if signal_type != SignalType.SELL:
            continue
        try:
            order = await _order_use_cases.place(
                PlaceOrderCommand(
                    stock_code=code,
                    order_type=OrderType.SELL,
                    quantity=1,
                    price=0,
                )
            )
            logger.info("[장 마감 매도] 주문 체결 — 종목=%s order_id=%s", code, order.order_id)
        except Exception as exc:
            logger.error("[장 마감 매도] 주문 실패 — 종목=%s: %s", code, exc)


async def job_daily_summary() -> None:
    """15:35 — 당일 체결 내역 요약 로그"""
    trades = await _order_use_cases.list_trades()
    today = date.today().isoformat()
    today_trades = [t for t in trades if t.traded_at.startswith(today)]

    logger.info(
        "[일일 요약] %s 체결 건수=%d",
        today,
        len(today_trades),
    )
    for t in today_trades:
        logger.info(
            "  ▶ %s %s × %d주 @ %d원",
            t.stock_code,
            t.order_type.value,
            t.quantity,
            t.price,
        )


def create_scheduler() -> AsyncIOScheduler:
    """FastAPI lifespan에서 호출하는 스케줄러 팩토리."""
    scheduler = AsyncIOScheduler(timezone="Asia/Seoul")

    # 평일(월~금)만 실행
    weekdays = "mon-fri"

    scheduler.add_job(
        job_morning_signal,
        CronTrigger(hour=9, minute=5, day_of_week=weekdays),
        id="morning_signal",
        name="장 시작 시그널 생성",
    )
    scheduler.add_job(
        job_morning_buy,
        CronTrigger(hour=9, minute=10, day_of_week=weekdays),
        id="morning_buy",
        name="장 시작 BUY 주문",
    )
    scheduler.add_job(
        job_close_sell,
        CronTrigger(hour=15, minute=20, day_of_week=weekdays),
        id="close_sell",
        name="장 마감 SELL 주문",
    )
    scheduler.add_job(
        job_daily_summary,
        CronTrigger(hour=15, minute=35, day_of_week=weekdays),
        id="daily_summary",
        name="일일 체결 내역 요약",
    )

    return scheduler
