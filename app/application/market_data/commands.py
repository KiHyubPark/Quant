from dataclasses import dataclass, field


@dataclass(frozen=True)
class SearchStocksCommand:
    keyword: str


@dataclass(frozen=True)
class GetCandlesCommand:
    code: str
    period: str = field(default="3mo")  # 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y
    count: int = field(default=100)


@dataclass(frozen=True)
class GetTickerCommand:
    code: str
