from fastapi import APIRouter, Depends, HTTPException

from app.application.portfolio.use_cases import PortfolioUseCases
from app.domain.portfolio.exceptions import PositionNotFoundError
from app.infrastructure.portfolio.portfolio_repository import InMemoryPortfolioRepository
from app.presentation.portfolio.schemas import BalanceSchema, PositionSchema

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])

_portfolio_repo = InMemoryPortfolioRepository()


def get_use_cases() -> PortfolioUseCases:
    return PortfolioUseCases(_portfolio_repo)


def _position_to_dict(pos) -> dict:
    return {
        "stock_code": pos.stock_code,
        "stock_name": pos.stock_name,
        "quantity": pos.quantity,
        "avg_price": pos.avg_price,
        "current_price": pos.current_price,
        "profit_loss": pos.profit_loss,
        "profit_loss_rate": pos.profit_loss_rate,
    }


@router.get("/balance", response_model=BalanceSchema, summary="계좌 잔고 조회")
async def get_balance(use_cases: PortfolioUseCases = Depends(get_use_cases)):
    balance = await use_cases.get_balance()
    return {
        "cash": balance.cash,
        "total_eval": balance.total_eval,
        "total_profit_loss": balance.total_profit_loss,
        "positions": [_position_to_dict(p) for p in balance.positions],
    }


@router.get("/positions", response_model=list[PositionSchema], summary="보유 종목 전체 조회")
async def list_positions(use_cases: PortfolioUseCases = Depends(get_use_cases)):
    positions = await use_cases.get_positions()
    return [_position_to_dict(p) for p in positions]


@router.get("/positions/{stock_code}", response_model=PositionSchema, summary="보유 종목 단건 조회")
async def get_position(
    stock_code: str,
    use_cases: PortfolioUseCases = Depends(get_use_cases),
):
    try:
        pos = await use_cases.get_position(stock_code)
        return _position_to_dict(pos)
    except PositionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
