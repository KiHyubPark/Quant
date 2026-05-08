from typing import Protocol
from app.domain.backtest.entity import BacktestResult


class BacktestRepository(Protocol):
    async def run(
        self,
        strategy_id: str,
        stock_code: str,
        start_date: str,
        end_date: str,
        initial_capital: int,
    ) -> BacktestResult: ...

    async def get(self, result_id: str) -> BacktestResult: ...
