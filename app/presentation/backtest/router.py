import asyncio

from fastapi import APIRouter, Depends, HTTPException

from app.application.backtest.commands import RunBacktestCommand
from app.application.backtest.use_cases import BacktestUseCases
from app.domain.backtest.exceptions import BacktestResultNotFoundError
from app.infrastructure.backtest.backtest_repository import PandasBacktestRepository
from app.presentation.backtest.schemas import (
    BacktestResultSchema,
    BatchBacktestItemSchema,
    BatchBacktestSchema,
    BatchBacktestSummarySchema,
    RunBacktestBatchSchema,
    RunBacktestSchema,
)

router = APIRouter(prefix="/backtest", tags=["Backtest"])

_backtest_repo = PandasBacktestRepository()


def get_use_cases() -> BacktestUseCases:
    return BacktestUseCases(_backtest_repo)


def _result_to_dict(result) -> dict:
    return {
        "result_id": result.result_id,
        "strategy_id": result.strategy_id,
        "stock_code": result.stock_code,
        "start_date": result.start_date,
        "end_date": result.end_date,
        "initial_capital": result.initial_capital,
        "final_capital": result.final_capital,
        "metrics": {
            "total_return": result.metrics.total_return,
            "annualized_return": result.metrics.annualized_return,
            "max_drawdown": result.metrics.max_drawdown,
            "sharpe_ratio": result.metrics.sharpe_ratio,
            "win_rate": result.metrics.win_rate,
            "total_trades": result.metrics.total_trades,
        },
    }


@router.post("/run", response_model=BacktestResultSchema, status_code=201, summary="백테스트 실행")
async def run_backtest(
    body: RunBacktestSchema,
    use_cases: BacktestUseCases = Depends(get_use_cases),
):
    try:
        result = await use_cases.run(
            RunBacktestCommand(
                strategy_id=body.strategy_id,
                stock_code=body.stock_code,
                start_date=body.start_date,
                end_date=body.end_date,
                initial_capital=body.initial_capital,
            )
        )
        return _result_to_dict(result)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/results/{result_id}", response_model=BacktestResultSchema, summary="백테스트 결과 조회")
async def get_result(
    result_id: str,
    use_cases: BacktestUseCases = Depends(get_use_cases),
):
    try:
        result = await use_cases.get(result_id)
        return _result_to_dict(result)
    except BacktestResultNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/run-batch",
    response_model=BatchBacktestSchema,
    status_code=201,
    summary="여러 종목 동시 백테스트",
)
async def run_backtest_batch(
    body: RunBacktestBatchSchema,
    use_cases: BacktestUseCases = Depends(get_use_cases),
):
    """주어진 전략으로 여러 종목을 한 번에 백테스트하고 비교 요약을 반환한다."""

    async def _run_one(code: str) -> BatchBacktestItemSchema:
        try:
            result = await use_cases.run(
                RunBacktestCommand(
                    strategy_id=body.strategy_id,
                    stock_code=code,
                    start_date=body.start_date,
                    end_date=body.end_date,
                    initial_capital=body.initial_capital,
                )
            )
            return BatchBacktestItemSchema(
                stock_code=code,
                success=True,
                result=_result_to_dict(result),
            )
        except (ValueError, Exception) as e:
            return BatchBacktestItemSchema(stock_code=code, success=False, error=str(e))

    items = await asyncio.gather(*(_run_one(c) for c in body.stock_codes))

    successful = [it for it in items if it.success and it.result is not None]
    if not successful:
        raise HTTPException(status_code=422, detail="모든 종목 백테스트에 실패했습니다.")

    metrics    = [it.result.metrics for it in successful]
    avg_return = sum(m.total_return for m in metrics) / len(metrics)
    avg_win    = sum(m.win_rate for m in metrics) / len(metrics)
    avg_trades = sum(m.total_trades for m in metrics) / len(metrics)

    best_idx  = max(range(len(successful)), key=lambda i: successful[i].result.metrics.total_return)
    worst_idx = min(range(len(successful)), key=lambda i: successful[i].result.metrics.total_return)

    return BatchBacktestSchema(
        summary=BatchBacktestSummarySchema(
            strategy_id=body.strategy_id,
            total_stocks=len(successful),
            avg_return=round(avg_return, 2),
            avg_win_rate=round(avg_win, 2),
            avg_trades=round(avg_trades, 2),
            best_stock=successful[best_idx].stock_code,
            worst_stock=successful[worst_idx].stock_code,
        ),
        items=items,
    )
