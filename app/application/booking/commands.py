from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BookingDatesCommand:
    checkin: str
    checkout: str


@dataclass(frozen=True)
class CreateBookingCommand:
    firstname: str
    lastname: str
    totalprice: int
    depositpaid: bool
    bookingdates: BookingDatesCommand
    additionalneeds: Optional[str] = None


@dataclass(frozen=True)
class PartialUpdateBookingCommand:
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    totalprice: Optional[int] = None
    depositpaid: Optional[bool] = None
    bookingdates: Optional[BookingDatesCommand] = None
    additionalneeds: Optional[str] = None
