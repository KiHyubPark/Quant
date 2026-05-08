from app.domain.portfolio.entity import Balance, Position
from app.domain.portfolio.repository import PortfolioRepository


class PortfolioUseCases:
    def __init__(self, repository: PortfolioRepository) -> None:
        self._repository = repository

    async def get_balance(self) -> Balance:
        return await self._repository.get_balance()

    async def get_positions(self) -> list[Position]:
        return await self._repository.get_positions()

    async def get_position(self, stock_code: str) -> Position:
        return await self._repository.get_position(stock_code)
