from dataclasses import dataclass

from app.domain.strategy.entity import StrategyId


@dataclass(frozen=True)
class CreateStrategyCommand:
    name: str
    description: str


@dataclass(frozen=True)
class GenerateSignalCommand:
    strategy_id: StrategyId
    stock_code: str
