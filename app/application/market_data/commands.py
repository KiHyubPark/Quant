from dataclasses import dataclass, field

from app.domain.market_data.entity import CandlePeriod


@dataclass(frozen=True)
class SearchStocksCommand:
    keyword: str


@dataclass(frozen=True)
class GetCandlesCommand:
    code: str
    period: CandlePeriod = field(default=CandlePeriod.THREE_MONTHS)
    count: int = field(default=100)


@dataclass(frozen=True)
class GetTickerCommand:
    code: str
