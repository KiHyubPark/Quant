from pydantic import BaseModel
from typing import Optional


class BookingDatesSchema(BaseModel):
    checkin: str
    checkout: str


class BookingCreateSchema(BaseModel):
    firstname: str
    lastname: str
    totalprice: int
    depositpaid: bool
    bookingdates: BookingDatesSchema
    additionalneeds: Optional[str] = None


class BookingPartialUpdateSchema(BaseModel):
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    totalprice: Optional[int] = None
    depositpaid: Optional[bool] = None
    bookingdates: Optional[BookingDatesSchema] = None
    additionalneeds: Optional[str] = None


class BookingResponseSchema(BaseModel):
    firstname: str
    lastname: str
    totalprice: int
    depositpaid: bool
    bookingdates: BookingDatesSchema
    additionalneeds: Optional[str] = None


class BookingWithIdResponseSchema(BaseModel):
    bookingid: int
    booking: BookingResponseSchema
