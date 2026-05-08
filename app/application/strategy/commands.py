from dataclasses import dataclass


@dataclass(frozen=True)
class CreateStrategyCommand:
    name: str
    description: str


@dataclass(frozen=True)
class GenerateSignalCommand:
    strategy_id: str
    stock_code: str
