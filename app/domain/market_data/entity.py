from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Stock:
    """종목 기본 정보"""
    code: str        # 종목 코드 (예: 005930)
    name: str        # 종목명
    market: str      # 시장 구분 (KOSPI / KOSDAQ)


@dataclass(frozen=True)
class Candle:
    """OHLCV 캔들 데이터"""
    date: str        # 날짜 (YYYYMMDD)
    open: int        # 시가
    high: int        # 고가
    low: int         # 저가
    close: int       # 종가
    volume: int      # 거래량


@dataclass(frozen=True)
class Ticker:
    """실시간 현재가"""
    code: str
    price: int
    change: int      # 전일 대비
    change_rate: float  # 등락률 (%)
