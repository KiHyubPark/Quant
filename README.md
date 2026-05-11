# Quant - KRX 주식 자동매매 시스템

KRX(한국거래소) 공식 데이터를 기반으로 한 FastAPI + DDD 구조의 퀀트 투자 시스템입니다.  
종목 검색, 캔들 조회, 전략 기반 시그널 생성, 백테스트, 주문/포트폴리오 관리를 제공합니다.

## 기술 스택

- **Python 3.13**
- **FastAPI** — 비동기 웹 프레임워크
- **pykrx** — KRX 공식 OHLCV 데이터
- **FinanceDataReader** — 전체 종목 목록 조회
- **pandas** — 백테스트 데이터 처리
- **APScheduler** — 자동매매 스케줄러
- **Pydantic v2** — 요청/응답 스키마 검증
- **Uvicorn** — ASGI 서버

## 프로젝트 구조

DDD(Domain-Driven Design) 4계층 아키텍처를 따릅니다.

```
app/
├── domain/{context}/
│   ├── entity.py          # 도메인 엔티티 (불변 dataclass)
│   ├── repository.py      # 레포지토리 인터페이스 (Protocol)
│   └── exceptions.py      # 도메인 예외
├── application/{context}/
│   ├── commands.py        # 커맨드 DTO
│   └── use_cases.py       # 비즈니스 로직
├── infrastructure/{context}/
│   └── *_repository.py    # 레포지토리 구현체 (pykrx 등)
├── presentation/{context}/
│   ├── router.py          # FastAPI 라우터
│   └── schemas.py         # Pydantic 스키마
├── scheduler/
│   └── trading_job.py     # 자동매매 스케줄 작업
├── config.py              # 환경변수 설정 (pydantic-settings)
└── main.py                # FastAPI 앱 진입점
```

**Bounded Contexts:** `market_data` · `strategy` · `order` · `portfolio` · `backtest`

## 환경 설정

```bash
cp .env.example .env
```

```env
# 자동매매 스케줄러 (KIS OpenAPI 연동 완료 후 true로 변경)
SCHEDULER_ENABLED=false
```

## 실행 방법

```bash
python3.13 -m venv .venv
source .venv/bin/activate      # macOS / Linux
# .venv\Scripts\activate       # Windows

pip install -r requirements.txt
uvicorn app.main:app --reload
```

서버 기동 후 `http://localhost:8000` 에서 접근할 수 있습니다.

## API 문서

| 문서 종류 | URL |
|-----------|-----|
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

## 엔드포인트 목록

### Market Data

| Method | URL | 설명 |
|--------|-----|------|
| `GET` | `/market-data/stocks/search?keyword=삼성` | 종목 검색 |
| `GET` | `/market-data/stocks/{code}/candles` | 캔들(OHLCV) 조회 |
| `GET` | `/market-data/stocks/{code}/ticker` | 현재가 조회 |

### Strategy

| Method | URL | 설명 |
|--------|-----|------|
| `GET` | `/strategies` | 전략 목록 조회 |
| `GET` | `/strategies/{strategy_id}` | 전략 단건 조회 |
| `POST` | `/strategies` | 전략 등록 |
| `GET` | `/strategies/{strategy_id}/signal?code=005930` | 매매 시그널 생성 |

기본 제공 전략: `golden-cross` · `rsi` · `bollinger`

### Order

| Method | URL | 설명 |
|--------|-----|------|
| `POST` | `/orders` | 주문 실행 |
| `DELETE` | `/orders/{order_id}` | 주문 취소 |
| `GET` | `/orders/{order_id}` | 주문 단건 조회 |
| `GET` | `/orders/trades` | 체결 내역 조회 |

### Portfolio

| Method | URL | 설명 |
|--------|-----|------|
| `GET` | `/portfolio/balance` | 계좌 잔고 조회 |
| `GET` | `/portfolio/positions` | 보유 종목 전체 조회 |
| `GET` | `/portfolio/positions/{stock_code}` | 보유 종목 단건 조회 |

### Backtest

| Method | URL | 설명 |
|--------|-----|------|
| `POST` | `/backtest/run` | 백테스트 실행 |
| `GET` | `/backtest/results/{result_id}` | 백테스트 결과 조회 |

### 기타

| Method | URL | 설명 |
|--------|-----|------|
| `GET` | `/health` | 헬스 체크 |

## 사용 예시

**시그널 생성 (삼성전자 RSI 전략)**

```bash
GET /strategies/rsi/signal?code=005930
```

```json
{
  "strategy_id": "rsi",
  "stock_code": "005930",
  "signal_type": "BUY",
  "generated_at": "2026-05-11T10:00:00+00:00",
  "reason": "RSI 28.5 — 과매도 구간"
}
```

**백테스트 실행**

```bash
POST /backtest/run
```

```json
{
  "strategy_id": "golden-cross",
  "stock_code": "005930",
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "initial_capital": 10000000
}
```
