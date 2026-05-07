---
name: ddd-fastapi
description: >
  Python FastAPI 프로젝트에서 DDD(Domain-Driven Design) 아키텍처를 적용할 때 사용하는 스킬.
  새 도메인/기능을 DDD 구조로 처음 만들거나, 기존 코드를 DDD로 리팩토링할 때 반드시 이 스킬을 활용한다.
  "DDD로 만들어줘", "도메인 추가해줘", "서비스 리팩토링", "레이어 분리", "유스케이스 추가",
  "레포지토리 패턴 적용" 같은 요청이 오면 즉시 이 스킬을 참고한다.
---

# DDD FastAPI 스킬

이 프로젝트는 Python + FastAPI 기반의 DDD 아키텍처를 따른다.
코드를 추가하거나 리팩토링할 때는 아래 규칙을 정확히 따른다.

---

## 레이어 구조

```
app/
├── domain/<domain>/
│   ├── __init__.py
│   ├── entity.py        # 불변 값 객체 (frozen dataclass)
│   ├── repository.py    # 인터페이스 (Protocol)
│   └── exceptions.py    # 도메인 예외
├── application/<domain>/
│   ├── __init__.py
│   ├── commands.py      # 입력 DTO (frozen dataclass)
│   └── use_cases.py     # 비즈니스 로직
├── infrastructure/<domain>/
│   ├── __init__.py
│   └── <impl>_repository.py  # Protocol 구현체
├── presentation/<domain>/
│   ├── __init__.py
│   ├── schemas.py       # Pydantic 요청/응답 스키마
│   └── router.py        # FastAPI 엔드포인트
├── config.py
└── main.py
```

---

## 레이어별 책임과 의존 방향

```
Presentation → Application → Domain ← Infrastructure
```

- **Domain**: 외부 의존성 없음. 비즈니스 개념만 표현.
- **Application**: Domain만 의존. "무엇을 할지" 결정.
- **Infrastructure**: Domain의 Protocol을 구현. 실제 I/O 처리.
- **Presentation**: Application을 호출. HTTP 입출력만 담당.

레이어를 건너뛰는 의존은 금지한다 (예: Presentation이 Infrastructure를 직접 import).

---

## 각 레이어 코드 패턴

### domain/entity.py
```python
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class MyEntity:
    field_a: str
    field_b: int
    optional_field: Optional[str] = None
```
- `frozen=True` 필수 — 불변 객체
- 외부 라이브러리 import 금지 (순수 Python만)

### domain/repository.py
```python
from typing import Protocol
from app.domain.<domain>.entity import MyEntity

class MyRepository(Protocol):
    async def get(self, id: int) -> MyEntity: ...
    async def create(self, entity: MyEntity) -> MyEntity: ...
    async def update(self, id: int, entity: MyEntity) -> MyEntity: ...
    async def delete(self, id: int) -> bool: ...
```
- `Protocol` 사용 — Java의 interface에 해당
- 메서드 바디는 `...` 으로만

### domain/exceptions.py
```python
class MyEntityNotFoundError(Exception):
    def __init__(self, entity_id: int) -> None:
        self.entity_id = entity_id
        super().__init__(f"항목을 찾을 수 없습니다. (id={entity_id})")
```

### application/commands.py
```python
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class CreateMyEntityCommand:
    field_a: str
    field_b: int
    optional_field: Optional[str] = None

@dataclass(frozen=True)
class PartialUpdateMyEntityCommand:
    field_a: Optional[str] = None
    field_b: Optional[int] = None
```
- Command는 유스케이스 입력 DTO
- `frozen=True` 필수

### application/use_cases.py
```python
from app.application.<domain>.commands import CreateMyEntityCommand
from app.domain.<domain>.entity import MyEntity
from app.domain.<domain>.repository import MyRepository

class MyUseCases:
    def __init__(self, repository: MyRepository) -> None:
        self._repo = repository

    async def get(self, entity_id: int) -> MyEntity:
        return await self._repo.get(entity_id)

    async def create(self, cmd: CreateMyEntityCommand) -> MyEntity:
        entity = MyEntity(
            field_a=cmd.field_a,
            field_b=cmd.field_b,
            optional_field=cmd.optional_field,
        )
        return await self._repo.create(entity)
```
- 생성자에서 `repository: MyRepository` 타입으로 받음 (Protocol 타입 힌트 사용)
- HTTP, DB 등 인프라 코드 절대 포함 금지

### infrastructure/<impl>_repository.py
```python
from app.domain.<domain>.entity import MyEntity
from app.domain.<domain>.exceptions import MyEntityNotFoundError
from app.domain.<domain>.repository import MyRepository

class HttpMyRepository:  # 또는 SqlMyRepository 등
    async def get(self, entity_id: int) -> MyEntity:
        # 실제 I/O 처리
        ...

    async def create(self, entity: MyEntity) -> MyEntity:
        ...
```
- `MyRepository` Protocol을 묵시적으로 구현 (Python은 명시적 implements 불필요)
- 외부 API 호출, DB 쿼리 등 실제 I/O는 여기서만

### presentation/schemas.py
```python
from pydantic import BaseModel
from typing import Optional

class CreateMyEntitySchema(BaseModel):
    field_a: str
    field_b: int
    optional_field: Optional[str] = None

class MyEntityResponseSchema(BaseModel):
    field_a: str
    field_b: int
    optional_field: Optional[str] = None
```
- Pydantic `BaseModel` 사용 — HTTP 요청/응답 검증용
- Entity(dataclass)와 별개로 존재 (Presentation 전용)

### presentation/router.py
```python
from dataclasses import asdict
from fastapi import APIRouter, Depends, HTTPException
from app.application.<domain>.commands import CreateMyEntityCommand
from app.application.<domain>.use_cases import MyUseCases
from app.domain.<domain>.exceptions import MyEntityNotFoundError
from app.infrastructure.<domain>.<impl>_repository import HttpMyRepository
from app.presentation.<domain>.schemas import CreateMyEntitySchema, MyEntityResponseSchema

router = APIRouter(prefix="/<domains>", tags=["MyDomain"])

def get_use_cases() -> MyUseCases:
    return MyUseCases(HttpMyRepository())

@router.post("/", response_model=MyEntityResponseSchema, status_code=201)
async def create(body: CreateMyEntitySchema, uc: MyUseCases = Depends(get_use_cases)):
    cmd = CreateMyEntityCommand(
        field_a=body.field_a,
        field_b=body.field_b,
        optional_field=body.optional_field,
    )
    return asdict(await uc.create(cmd))
```
- `Depends(get_use_cases)` 로 의존성 주입
- Entity → dict 변환은 `asdict()` 사용
- 도메인 예외를 `HTTPException`으로 변환하는 책임은 여기서

---

## 신규 도메인 추가 절차

1. `domain/<domain>/` — entity, repository Protocol, exceptions 작성
2. `application/<domain>/` — commands, use_cases 작성
3. `infrastructure/<domain>/` — 실제 구현체 작성
4. `presentation/<domain>/` — schemas, router 작성
5. `app/main.py` 에 `app.include_router(router)` 추가
6. 각 디렉터리에 `__init__.py` 생성

---

## 기존 코드 리팩토링 절차

1. **현재 코드 파악**: 기존 모델/서비스/라우터가 무엇을 하는지 읽는다
2. **레이어 매핑 결정**:
   - Pydantic 모델 → `presentation/schemas.py` (요청/응답용) + `domain/entity.py` (비즈니스 객체)
   - 서비스 클래스 → `application/use_cases.py` (비즈니스 로직) + `infrastructure/` (I/O 로직)
   - 라우터 → `presentation/router.py`
3. **Domain부터 작성** — 외부 의존성 없는 레이어부터 안→밖 순서로 작성
4. **기존 파일 삭제** — 새 구조가 완전히 동작 확인 후 제거
5. **main.py 라우터 경로 업데이트**

---

## 금지 사항

| 금지 | 이유 |
|------|------|
| Entity에 Pydantic BaseModel 사용 | Domain은 웹 프레임워크에 의존하면 안 됨 |
| Use Case에서 httpx/DB 직접 호출 | I/O는 Infrastructure 전용 |
| Presentation에서 Infrastructure 직접 import | 레이어 건너뜀 |
| Entity를 mutable로 만들기 | 불변 객체 원칙 위반 |
| `frozen=True` 없는 Command/Entity | 입력 DTO도 불변이어야 함 |