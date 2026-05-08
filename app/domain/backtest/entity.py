from dataclasses import dataclass


@dataclass(frozen=True)
class PerformanceMetrics:
    """백테스트 성과 지표"""
    total_return: float      # 총 수익률 (%)
    annualized_return: float # 연환산 수익률 (%)
    max_drawdown: float      # 최대 낙폭 (%)
    sharpe_ratio: float      # 샤프 지수
    win_rate: float          # 승률 (%)
    total_trades: int        # 총 거래 횟수


@dataclass(frozen=True)
class BacktestResult:
    """백테스트 결과"""
    result_id: str
    strategy_id: str
    stock_code: str
    start_date: str          # YYYYMMDD
    end_date: str            # YYYYMMDD
    initial_capital: int     # 초기 자본
    final_capital: int       # 최종 자본
    metrics: PerformanceMetrics
