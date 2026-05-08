from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, Query

from app.application.strategy.commands import CreateStrategyCommand, GenerateSignalCommand
from app.application.strategy.use_cases import StrategyUseCases
from app.domain.strategy.exceptions import StrategyNotFoundError
from app.infrastructure.market_data.market_data_repository import PykrxMarketDataRepository
from app.infrastructure.strategy.strategy_repository import InMemoryStrategyRepository
from app.presentation.strategy.schemas import CreateStrategySchema, SignalSchema, StrategySchema

router = APIRouter(prefix="/strategies", tags=["Strategy"])

# 서버 재시작 시 초기화되지 않도록 모듈 레벨에서 싱글턴 유지
_market_data_repo = PykrxMarketDataRepository()
_strategy_repo = InMemoryStrategyRepository(_market_data_repo)


def get_use_cases() -> StrategyUseCases:
    return StrategyUseCases(_strategy_repo)


@router.get("", response_model=list[StrategySchema], summary="전략 목록 조회")
async def list_strategies(use_cases: StrategyUseCases = Depends(get_use_cases)):
    strategies = await use_cases.list()
    return [asdict(s) for s in strategies]


@router.get("/{strategy_id}", response_model=StrategySchema, summary="전략 단건 조회")
async def get_strategy(
    strategy_id: str,
    use_cases: StrategyUseCases = Depends(get_use_cases),
):
    try:
        strategy = await use_cases.get(strategy_id)
        return asdict(strategy)
    except StrategyNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=StrategySchema, status_code=201, summary="전략 등록")
async def create_strategy(
    body: CreateStrategySchema,
    use_cases: StrategyUseCases = Depends(get_use_cases),
):
    strategy = await use_cases.create(CreateStrategyCommand(name=body.name, description=body.description))
    return asdict(strategy)


@router.get("/{strategy_id}/signal", response_model=SignalSchema, summary="매매 시그널 생성")
async def generate_signal(
    strategy_id: str,
    code: str = Query(..., description="종목 코드 (예: 005930)"),
    use_cases: StrategyUseCases = Depends(get_use_cases),
):
    try:
        signal = await use_cases.generate_signal(GenerateSignalCommand(strategy_id=strategy_id, stock_code=code))
        return asdict(signal)
    except StrategyNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
