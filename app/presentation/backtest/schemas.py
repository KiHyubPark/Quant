from pydantic import BaseModel, Field


class RunBacktestSchema(BaseModel):
    strategy_id: str
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
    strategy_id: str
    stock_code: str
    start_date: str
    end_date: str
    initial_capital: int
    final_capital: int
    metrics: PerformanceMetricsSchema
