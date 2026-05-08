from fastapi import APIRouter, Depends, HTTPException

from app.application.backtest.commands import RunBacktestCommand
from app.application.backtest.use_cases import BacktestUseCases
from app.domain.backtest.exceptions import BacktestResultNotFoundError
from app.infrastructure.backtest.backtest_repository import PandasBacktestRepository
from app.presentation.backtest.schemas import BacktestResultSchema, RunBacktestSchema

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
