# Quant - Restful Booker CRUD API

[restful-booker.herokuapp.com](https://restful-booker.herokuapp.com) 의 공개 API를 활용한 FastAPI 기반 예약 관리 CRUD 서비스입니다.

## 기술 스택

- **Python 3.13**
- **FastAPI** — 비동기 웹 프레임워크
- **httpx** — 비동기 HTTP 클라이언트 (외부 API 연동)
- **Pydantic v2** — 요청/응답 스키마 검증
- **Uvicorn** — ASGI 서버

## 프로젝트 구조

```
app/
├── config.py               # 환경변수 설정 (pydantic-settings)
├── main.py                 # FastAPI 앱 진입점
├── models/
│   └── booking.py          # 요청/응답 Pydantic 스키마
├── routers/
│   └── booking.py          # 라우터 (엔드포인트 정의)
└── services/
    └── booking_service.py  # httpx 비동기 클라이언트 & 토큰 인증 처리
```

## 환경 설정

프로젝트 루트에 `.env` 파일을 생성합니다.

```bash
cp .env.example .env  # 또는 아래 내용으로 직접 생성
```

```env
BOOKER_BASE_URL=https://restful-booker.herokuapp.com
BOOKER_USERNAME=admin
BOOKER_PASSWORD=password123
```

> PUT / PATCH / DELETE 요청은 restful-booker API 토큰 인증이 필요합니다.  
> 위 기본값(`admin` / `password123`)이 공식 테스트 계정입니다.

## 실행 방법

### 1. 가상환경 생성 및 패키지 설치

```bash
python3.13 -m venv .venv
source .venv/bin/activate      # macOS / Linux
# .venv\Scripts\activate       # Windows

pip install -r requirements.txt
```

### 2. 서버 실행

```bash
uvicorn app.main:app --reload
```

서버가 기동되면 `http://localhost:8000` 에서 접근할 수 있습니다.

## API 문서 (Swagger UI)

서버 실행 후 브라우저에서 아래 주소로 접속합니다.

| 문서 종류 | URL |
|-----------|-----|
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

## 엔드포인트 목록

| Method | URL | 설명 |
|--------|-----|------|
| `GET` | `/bookings/` | 전체 예약 ID 목록 조회 |
| `GET` | `/bookings/{id}` | 예약 단건 상세 조회 |
| `POST` | `/bookings/` | 신규 예약 생성 |
| `PUT` | `/bookings/{id}` | 예약 전체 수정 (인증 필요) |
| `PATCH` | `/bookings/{id}` | 예약 부분 수정 (인증 필요) |
| `DELETE` | `/bookings/{id}` | 예약 삭제 (인증 필요) |
| `GET` | `/health` | 헬스 체크 |

### 요청 예시

**예약 생성 (POST /bookings/)**

```json
{
  "firstname": "Gihyeob",
  "lastname": "Park",
  "totalprice": 150,
  "depositpaid": true,
  "bookingdates": {
    "checkin": "2026-06-01",
    "checkout": "2026-06-05"
  },
  "additionalneeds": "Breakfast"
}
```

**예약 부분 수정 (PATCH /bookings/{id})**

```json
{
  "totalprice": 200,
  "additionalneeds": "Lunch"
}
```
