from fastapi import FastAPI
from app.routers import booking

app = FastAPI(
    title="Restful Booker CRUD",
    description="https://restful-booker.herokuapp.com API를 활용한 예약 관리 서비스",
    version="0.1.0",
)

app.include_router(booking.router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
