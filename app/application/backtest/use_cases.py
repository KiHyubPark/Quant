from app.application.backtest.commands import RunBacktestCommand
from app.domain.backtest.entity import BacktestResult
from app.domain.backtest.repository import BacktestRepository


class BacktestUseCases:
    def __init__(self, repository: BacktestRepository) -> None:
        self._repository = repository

    async def run(self, command: RunBacktestCommand) -> BacktestResult:
        return await self._repository.run(
            strategy_id=command.strategy_id,
            stock_code=command.stock_code,
            start_date=command.start_date,
            end_date=command.end_date,
            initial_capital=command.initial_capital,
        )

    async def get(self, result_id: str) -> BacktestResult:
        return await self._repository.get(result_id)
