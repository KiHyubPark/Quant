from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BookingDates:
    checkin: str
    checkout: str


@dataclass(frozen=True)
class Booking:
    firstname: str
    lastname: str
    totalprice: int
    depositpaid: bool
    bookingdates: BookingDates
    additionalneeds: Optional[str] = None


@dataclass(frozen=True)
class BookingWithId:
    bookingid: int
    booking: Booking
