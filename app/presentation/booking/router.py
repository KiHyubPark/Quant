from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.booking.commands import (
    BookingDatesCommand,
    CreateBookingCommand,
    PartialUpdateBookingCommand,
)


from app.application.booking.use_cases import BookingUseCases
from app.domain.booking.exceptions import BookingNotFoundError
from app.infrastructure.booking.http_repository import HttpBookingRepository
from app.presentation.booking.schemas import (
    BookingCreateSchema,
    BookingPartialUpdateSchema,
    BookingResponseSchema,
    BookingWithIdResponseSchema,
)

router = APIRouter(prefix="/bookings", tags=["Bookings"])


def get_use_cases() -> BookingUseCases:
    return BookingUseCases(HttpBookingRepository())


@router.get("/", summary="전체 예약 목록 조회")
async def list_bookings(use_cases: BookingUseCases = Depends(get_use_cases)):
    return await use_cases.list_bookings()


@router.get("/{booking_id}", response_model=BookingResponseSchema, summary="예약 단건 조회")
async def get_booking(booking_id: int, use_cases: BookingUseCases = Depends(get_use_cases)):
    try:
        return asdict(await use_cases.get_booking(booking_id))
    except BookingNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/",
    response_model=BookingWithIdResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="예약 생성",
)
async def create_booking(
    body: BookingCreateSchema,
    use_cases: BookingUseCases = Depends(get_use_cases),
):
    cmd = CreateBookingCommand(
        firstname=body.firstname,
        lastname=body.lastname,
        totalprice=body.totalprice,
        depositpaid=body.depositpaid,
        bookingdates=BookingDatesCommand(
            checkin=body.bookingdates.checkin,
            checkout=body.bookingdates.checkout,
        ),
        additionalneeds=body.additionalneeds,
    )
    result = await use_cases.create_booking(cmd)
    return asdict(result)


@router.put("/{booking_id}", response_model=BookingResponseSchema, summary="예약 전체 수정")
async def update_booking(
    booking_id: int,
    body: BookingCreateSchema,
    use_cases: BookingUseCases = Depends(get_use_cases),
):
    cmd = CreateBookingCommand(
        firstname=body.firstname,
        lastname=body.lastname,
        totalprice=body.totalprice,
        depositpaid=body.depositpaid,
        bookingdates=BookingDatesCommand(
            checkin=body.bookingdates.checkin,
            checkout=body.bookingdates.checkout,
        ),
        additionalneeds=body.additionalneeds,
    )
    try:
        return asdict(await use_cases.update_booking(booking_id, cmd))
    except BookingNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{booking_id}", response_model=BookingResponseSchema, summary="예약 부분 수정")
async def partial_update_booking(
    booking_id: int,
    body: BookingPartialUpdateSchema,
    use_cases: BookingUseCases = Depends(get_use_cases),
):
    cmd = PartialUpdateBookingCommand(
        firstname=body.firstname,
        lastname=body.lastname,
        totalprice=body.totalprice,
        depositpaid=body.depositpaid,
        bookingdates=BookingDatesCommand(
            checkin=body.bookingdates.checkin,
            checkout=body.bookingdates.checkout,
        ) if body.bookingdates else None,
        additionalneeds=body.additionalneeds,
    )
    if not any(asdict(cmd).values()):
        raise HTTPException(status_code=400, detail="수정할 필드를 하나 이상 입력해주세요.")
    try:
        return asdict(await use_cases.partial_update_booking(booking_id, cmd))
    except BookingNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT, summary="예약 삭제")
async def delete_booking(booking_id: int, use_cases: BookingUseCases = Depends(get_use_cases)):
    deleted = await use_cases.delete_booking(booking_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="예약을 찾을 수 없습니다.")
