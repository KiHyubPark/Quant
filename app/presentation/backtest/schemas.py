from pydantic import BaseModel, Field

from app.domain.strategy.entity import StrategyId


class RunBacktestSchema(BaseModel):
    strategy_id: StrategyId
    stock_code: str
    start_date: str = Field(..., description="시작일 (YYYYMMDD)")
    end_date: str = Field(..., description="종료일 (YYYYMMDD)")
    initial_capital: int = Field(default=10_000_000, gt=0, description="초기 자본 (원)")


class PerformanceMetricsSchema(BaseModel):
    total_return: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int


class BacktestResultSchema(BaseModel):
    result_id: str
    strategy_id: StrategyId
    stock_code: str
    start_date: str
    end_date: str
    initial_capital: int
    final_capital: int
    metrics: PerformanceMetricsSchema


class RunBacktestBatchSchema(BaseModel):
    strategy_id: StrategyId
    stock_codes: list[str] = Field(..., min_length=1, description="종목 코드 목록")
    start_date: str = Field(..., description="시작일 (YYYYMMDD)")
    end_date: str = Field(..., description="종료일 (YYYYMMDD)")
    initial_capital: int = Field(default=10_000_000, gt=0, description="종목당 초기 자본 (원)")


class BatchBacktestItemSchema(BaseModel):
    stock_code: str
    success: bool
    result: BacktestResultSchema | None = None
    error: str | None = None


class BatchBacktestSummarySchema(BaseModel):
    strategy_id: StrategyId
    total_stocks: int
    avg_return: float
    avg_win_rate: float
    avg_trades: float
    best_stock: str | None
    worst_stock: str | None


class BatchBacktestSchema(BaseModel):
    summary: BatchBacktestSummarySchema
    items: list[BatchBacktestItemSchema]
