from pydantic import BaseModel
from typing import Optional


class BookingDates(BaseModel):
    checkin: str   # "YYYY-MM-DD"
    checkout: str  # "YYYY-MM-DD"


class BookingCreate(BaseModel):
    firstname: str
    lastname: str
    totalprice: int
    depositpaid: bool
    bookingdates: BookingDates
    additionalneeds: Optional[str] = None


class BookingUpdate(BaseModel):
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    totalprice: Optional[int] = None
    depositpaid: Optional[bool] = None
    bookingdates: Optional[BookingDates] = None
    additionalneeds: Optional[str] = None


class BookingResponse(BookingCreate):
    pass


class BookingIdResponse(BaseModel):
    bookingid: int
    booking: BookingResponse
