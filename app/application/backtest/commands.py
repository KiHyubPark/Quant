from dataclasses import dataclass, field

from app.domain.strategy.entity import StrategyId


@dataclass(frozen=True)
class RunBacktestCommand:
    strategy_id: StrategyId
    stock_code: str
    start_date: str       # YYYYMMDD
    end_date: str         # YYYYMMDD
    initial_capital: int = field(default=10_000_000)
