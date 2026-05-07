from fastapi import APIRouter, HTTPException, status
from app.models.booking import BookingCreate, BookingUpdate
from app.services.booking_service import booking_service
import httpx

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.get("/", summary="전체 예약 목록 조회")
async def list_bookings():
    return await booking_service.list_bookings()


@router.get("/{booking_id}", summary="예약 단건 조회")
async def get_booking(booking_id: int):
    try:
        return await booking_service.get_booking(booking_id)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="예약을 찾을 수 없습니다.")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))


@router.post("/", status_code=status.HTTP_201_CREATED, summary="예약 생성")
async def create_booking(body: BookingCreate):
    try:
        return await booking_service.create_booking(body.model_dump())
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))


@router.put("/{booking_id}", summary="예약 전체 수정")
async def update_booking(booking_id: int, body: BookingCreate):
    try:
        return await booking_service.update_booking(booking_id, body.model_dump())
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="예약을 찾을 수 없습니다.")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))


@router.patch("/{booking_id}", summary="예약 부분 수정")
async def partial_update_booking(booking_id: int, body: BookingUpdate):
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="수정할 필드를 하나 이상 입력해주세요.")
    try:
        return await booking_service.partial_update_booking(booking_id, data)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="예약을 찾을 수 없습니다.")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT, summary="예약 삭제")
async def delete_booking(booking_id: int):
    try:
        deleted = await booking_service.delete_booking(booking_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="예약을 찾을 수 없습니다.")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
