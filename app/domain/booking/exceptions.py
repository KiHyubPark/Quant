class BookingNotFoundError(Exception):
    def __init__(self, booking_id: int) -> None:
        self.booking_id = booking_id
        super().__init__(f"예약을 찾을 수 없습니다. (id={booking_id})")
