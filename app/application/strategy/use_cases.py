from app.application.strategy.commands import CreateStrategyCommand, GenerateSignalCommand
from app.domain.strategy.entity import Signal, Strategy
from app.domain.strategy.repository import StrategyRepository


class StrategyUseCases:
    def __init__(self, repository: StrategyRepository) -> None:
        self._repository = repository

    async def list(self) -> list[Strategy]:
        return await self._repository.list()

    async def get(self, strategy_id: str) -> Strategy:
        return await self._repository.get(strategy_id)

    async def create(self, command: CreateStrategyCommand) -> Strategy:
        import uuid
        strategy = Strategy(
            id=str(uuid.uuid4()),
            name=command.name,
            description=command.description,
        )
        return await self._repository.save(strategy)

    async def generate_signal(self, command: GenerateSignalCommand) -> Signal:
        return await self._repository.generate_signal(command.strategy_id, command.stock_code)
