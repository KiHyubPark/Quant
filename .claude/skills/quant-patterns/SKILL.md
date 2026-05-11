---
name: quant-patterns
description: Quant 프로젝트의 DDD 기반 FastAPI 주식 자동매매 시스템 코딩 패턴
version: 1.0.0
source: local-git-analysis
analyzed_commits: 12
---

# Quant 프로젝트 패턴

## 커밋 컨벤션

Conventional Commits 형식을 따른다:

- `feat:` — 새 기능 (API 엔드포인트, 전략 추가 등)
- `fix:` — 버그 수정 (데이터 소스 교체, 오류 수정)
- `refactor:` — 동작 변경 없는 코드 개선 (Enum 전환, 파일 분리 등)
- `docs:` — 문서 업데이트
- `chore:` — 빌드/설정 작업

## 아키텍처: DDD + 계층형 구조

```
app/
├── domain/{bounded_context}/
│   ├── entity.py          # 도메인 엔티티 (dataclass frozen=True)
│   ├── repository.py      # 추상 레포지토리 인터페이스 (Protocol)
│   └── exceptions.py      # 도메인 예외
├── application/{bounded_context}/
│   ├── commands.py        # 커맨드 DTO (dataclass frozen=True)
│   └── use_cases.py       # 유즈케이스 (비즈니스 로직)
├── infrastructure/{bounded_context}/
│   └── {name}_repository.py  # 레포지토리 구현체 (pykrx, DB 등)
├── presentation/{bounded_context}/
│   ├── router.py          # FastAPI 라우터
│   └── schemas.py         # Pydantic 스키마 (요청/응답)
└── main.py                # FastAPI 앱 초기화 및 라우터 등록
```

**Bounded Contexts:**
- `market_data` — KRX 시장 데이터 (종목, 캔들, 현재가)
- `strategy` — 매매 전략 및 시그널 생성
- `order` — 매매 주문
- `portfolio` — 포트폴리오 관리
- `backtest` — 백테스트

## 핵심 패턴

### 1. 도메인 엔티티: 불변 dataclass

```python
from dataclasses import dataclass
from enum import Enum

class CandlePeriod(str, Enum):
    ONE_MONTH = "1mo"
    THREE_MONTHS = "3mo"

@dataclass(frozen=True)
class Candle:
    date: str
    open: int
    high: int
    low: int
    close: int
    volume: int
```

- 항상 `@dataclass(frozen=True)` 사용 → 불변성 보장
- Enum은 `str, Enum` 상속 → FastAPI 쿼리 파라미터로 직접 사용 가능
- 도메인 예외는 별도 `exceptions.py`에 정의

### 2. 커맨드 DTO

```python
from dataclasses import dataclass, field
from app.domain.market_data.entity import CandlePeriod

@dataclass(frozen=True)
class GetCandlesCommand:
    code: str
    period: CandlePeriod = field(default=CandlePeriod.THREE_MONTHS)
    count: int = field(default=100)
```

- 커맨드도 `frozen=True` dataclass
- 기본값은 `field(default=...)` 사용

### 3. 레포지토리 패턴

**추상 인터페이스 (domain):**
```python
from typing import Protocol

class MarketDataRepository(Protocol):
    async def search_stocks(self, keyword: str) -> list[Stock]: ...
    async def get_candles(self, code: str, period: CandlePeriod, count: int) -> list[Candle]: ...
    async def get_ticker(self, code: str) -> Ticker: ...
```

**구현체 (infrastructure):**
```python
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

_executor = ThreadPoolExecutor(max_workers=4)
_cache: dict | None = None
_cache_lock = threading.Lock()

class PykrxMarketDataRepository:
    async def get_candles(self, code: str, period: CandlePeriod, count: int) -> list[Candle]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(_executor, self._sync_get_candles, code, period, count)

    def _sync_get_candles(self, code: str, period: CandlePeriod, count: int) -> list[Candle]:
        # 동기 블로킹 I/O는 _sync_ 접두사 메서드로 분리
        ...
```

- `asyncio.get_running_loop()` 사용 (`get_event_loop()` 사용 금지)
- 블로킹 I/O는 `ThreadPoolExecutor`로 실행
- 동기 메서드는 `_sync_` 접두사
- 글로벌 캐시는 `threading.Lock()` + double-checked locking으로 보호

### 4. 유즈케이스

```python
class MarketDataUseCases:
    def __init__(self, repository: MarketDataRepository) -> None:
        self._repository = repository

    async def get_candles(self, command: GetCandlesCommand) -> list[Candle]:
        return await self._repository.get_candles(
            command.code, command.period, command.count
        )
```

- 생성자에서 레포지토리 주입 (의존성 역전)
- 유즈케이스는 커맨드 객체를 받아 도메인 객체를 반환

### 5. FastAPI 라우터

```python
from dataclasses import asdict
from fastapi import APIRouter, Depends, HTTPException, Query

router = APIRouter(prefix="/market-data", tags=["Market Data"])

def get_use_cases() -> MarketDataUseCases:
    return MarketDataUseCases(PykrxMarketDataRepository())

@router.get("/stocks/{code}/candles", response_model=list[CandleSchema])
async def get_candles(
    code: str,
    period: CandlePeriod = Query(CandlePeriod.THREE_MONTHS),
    count: int = Query(100, ge=1, le=1000),
    use_cases: MarketDataUseCases = Depends(get_use_cases),
):
    try:
        candles = await use_cases.get_candles(GetCandlesCommand(code=code, period=period, count=count))
        return [asdict(c) for c in candles]
    except StockNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

- `Depends(get_use_cases)`로 의존성 주입
- 도메인 예외 → HTTP 예외로 변환
- `dataclasses.asdict()`로 응답 직렬화
- Enum 타입을 `Query` 파라미터로 직접 사용

### 6. 전략 패턴: 계산기 분리

전략 계산 로직은 별도 모듈로 분리한다:

```
infrastructure/strategy/
├── strategy_repository.py      # 전략 저장소 + 시그널 생성 조율
└── calculators/
    ├── __init__.py
    ├── golden_cross.py         # MA5/MA20 골든크로스
    ├── rsi.py                  # RSI 14일
    └── bollinger.py            # 볼린저밴드
```

각 계산기는 `calculate(prices: list[float]) -> tuple[SignalType, str]` 시그니처를 따른다:

```python
# calculators/rsi.py
def calculate(prices: list[float]) -> tuple[SignalType, str]:
    ...
    return SignalType.BUY, "RSI 28.5 — 과매도 구간"
```

전략 ID → 계산 함수 매핑:
```python
_SIGNAL_CALCULATORS: dict[StrategyId, Callable] = {
    StrategyId.GOLDEN_CROSS: golden_cross.calculate,
    StrategyId.RSI:          rsi.calculate,
    StrategyId.BOLLINGER:    bollinger.calculate,
}
```

## 새 기능 추가 워크플로우

### 새 Bounded Context 추가

1. `domain/{name}/entity.py` — 엔티티, Enum 정의
2. `domain/{name}/repository.py` — Protocol 인터페이스
3. `domain/{name}/exceptions.py` — 도메인 예외
4. `application/{name}/commands.py` — 커맨드 DTO
5. `application/{name}/use_cases.py` — 유즈케이스
6. `infrastructure/{name}/{name}_repository.py` — 구현체
7. `presentation/{name}/schemas.py` — Pydantic 스키마
8. `presentation/{name}/router.py` — FastAPI 라우터
9. `app/main.py` — 라우터 등록

### 새 전략 추가

1. `infrastructure/strategy/calculators/{name}.py` 생성
   - `calculate(prices: list[float]) -> tuple[SignalType, str]` 구현
2. `domain/strategy/entity.py`의 `StrategyId` Enum에 추가
3. `infrastructure/strategy/strategy_repository.py`에서:
   - `_DEFAULT_STRATEGIES`에 `Strategy(...)` 추가
   - `_SIGNAL_CALCULATORS`에 매핑 추가

### Enum 추가/변경

- 새 값 추가 후 관련 `presentation/*/schemas.py` 확인
- `str, Enum` 상속으로 FastAPI 쿼리 파라미터, 응답 직렬화 자동 지원

## 데이터 소스

- **pykrx** — KRX 공식 OHLCV 데이터 (`krx.get_market_ohlcv`)
- **FinanceDataReader** — 전체 종목 목록 (`fdr.StockListing("KRX")`)
  - pykrx의 `get_market_ticker_list`는 KRX API 변경에 취약하므로 FDR 사용
- **APScheduler** — 자동매매 스케줄러 (`SCHEDULER_ENABLED` 환경변수로 제어)

## 환경 설정

```python
# app/config.py — pydantic-settings 사용
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SCHEDULER_ENABLED: bool = False
    ...
```

`.env.example`에 필요한 환경변수를 명시한다.
