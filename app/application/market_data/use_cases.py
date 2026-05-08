from app.application.market_data.commands import GetCandlesCommand, GetTickerCommand, SearchStocksCommand
from app.domain.market_data.entity import Candle, Stock, Ticker
from app.domain.market_data.repository import MarketDataRepository


class MarketDataUseCases:
    def __init__(self, repository: MarketDataRepository) -> None:
        self._repository = repository

    async def search_stocks(self, command: SearchStocksCommand) -> list[Stock]:
        return await self._repository.search_stocks(command.keyword)

    async def get_candles(self, command: GetCandlesCommand) -> list[Candle]:
        return await self._repository.get_candles(command.code, command.period, command.count)

    async def get_ticker(self, command: GetTickerCommand) -> Ticker:
        return await self._repository.get_ticker(command.code)
