from dataclasses import asdict

from app.application.booking.commands import CreateBookingCommand, PartialUpdateBookingCommand
from app.domain.booking.entity import Booking, BookingDates, BookingWithId
from app.domain.booking.repository import BookingRepository


class BookingUseCases:
    def __init__(self, repository: BookingRepository) -> None:
        self._repo = repository

    async def list_bookings(self) -> list[dict]:
        return await self._repo.list()

    async def get_booking(self, booking_id: int) -> Booking:
        return await self._repo.get(booking_id)

    async def create_booking(self, cmd: CreateBookingCommand) -> BookingWithId:
        booking = Booking(
            firstname=cmd.firstname,
            lastname=cmd.lastname,
            totalprice=cmd.totalprice,
            depositpaid=cmd.depositpaid,
            bookingdates=BookingDates(
                checkin=cmd.bookingdates.checkin,
                checkout=cmd.bookingdates.checkout,
            ),
            additionalneeds=cmd.additionalneeds,
        )
        return await self._repo.create(booking)

    async def update_booking(self, booking_id: int, cmd: CreateBookingCommand) -> Booking:
        booking = Booking(
            firstname=cmd.firstname,
            lastname=cmd.lastname,
            totalprice=cmd.totalprice,
            depositpaid=cmd.depositpaid,
            bookingdates=BookingDates(
                checkin=cmd.bookingdates.checkin,
                checkout=cmd.bookingdates.checkout,
            ),
            additionalneeds=cmd.additionalneeds,
        )
        return await self._repo.update(booking_id, booking)

    async def partial_update_booking(self, booking_id: int, cmd: PartialUpdateBookingCommand) -> Booking:
        data = {k: v for k, v in asdict(cmd).items() if v is not None}
        return await self._repo.partial_update(booking_id, data)

    async def delete_booking(self, booking_id: int) -> bool:
        return await self._repo.delete(booking_id)
