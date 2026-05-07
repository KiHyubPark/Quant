import httpx
from typing import Optional

from app.config import settings
from app.domain.booking.entity import Booking, BookingDates, BookingWithId
from app.domain.booking.exceptions import BookingNotFoundError


class HttpBookingRepository:
    def __init__(self) -> None:
        self._base_url = settings.booker_base_url
        self._token: Optional[str] = None

    async def _get_token(self) -> str:
        if self._token:
            return self._token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/auth",
                json={
                    "username": settings.booker_username,
                    "password": settings.booker_password,
                },
            )
            response.raise_for_status()
            self._token = response.json()["token"]
            print(f"발급된 토큰: {self._token}")
            return self._token

    async def _auth_headers(self) -> dict:
        token = await self._get_token()
        return {"Cookie": f"token={token}"}

    # ── Read ────────────────────────────────────────────────────────────────

    async def list(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self._base_url}/booking")
            response.raise_for_status()
            return response.json()

    async def get(self, booking_id: int) -> Booking:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._base_url}/booking/{booking_id}",
                headers={"Accept": "application/json"},
            )
            if response.status_code == 404:
                raise BookingNotFoundError(booking_id)
            response.raise_for_status()
            data = response.json()
            return _to_entity(data)

    # ── Create ──────────────────────────────────────────────────────────────

    async def create(self, booking: Booking) -> BookingWithId:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/booking",
                json=_from_entity(booking),
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
            return BookingWithId(
                bookingid=data["bookingid"],
                booking=_to_entity(data["booking"]),
            )

    # ── Update ──────────────────────────────────────────────────────────────

    async def update(self, booking_id: int, booking: Booking) -> Booking:
        headers = await self._auth_headers()
        headers["Accept"] = "application/json"

        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self._base_url}/booking/{booking_id}",
                json=_from_entity(booking),
                headers=headers,
            )
            if response.status_code == 404:
                raise BookingNotFoundError(booking_id)
            response.raise_for_status()
            return _to_entity(response.json())

    async def partial_update(self, booking_id: int, data: dict) -> Booking:
        headers = await self._auth_headers()
        headers["Accept"] = "application/json"

        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self._base_url}/booking/{booking_id}",
                json=data,
                headers=headers,
            )
            if response.status_code == 404:
                raise BookingNotFoundError(booking_id)
            response.raise_for_status()
            return _to_entity(response.json())

    # ── Delete ──────────────────────────────────────────────────────────────

    async def delete(self, booking_id: int) -> bool:
        headers = await self._auth_headers()

        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self._base_url}/booking/{booking_id}",
                headers=headers,
            )
            return response.status_code == 201


# ── Helpers ──────────────────────────────────────────────────────────────────

def _to_entity(data: dict) -> Booking:
    return Booking(
        firstname=data["firstname"],
        lastname=data["lastname"],
        totalprice=data["totalprice"],
        depositpaid=data["depositpaid"],
        bookingdates=BookingDates(
            checkin=data["bookingdates"]["checkin"],
            checkout=data["bookingdates"]["checkout"],
        ),
        additionalneeds=data.get("additionalneeds"),
    )


def _from_entity(booking: Booking) -> dict:
    payload: dict = {
        "firstname": booking.firstname,
        "lastname": booking.lastname,
        "totalprice": booking.totalprice,
        "depositpaid": booking.depositpaid,
        "bookingdates": {
            "checkin": booking.bookingdates.checkin,
            "checkout": booking.bookingdates.checkout,
        },
    }
    if booking.additionalneeds is not None:
        payload["additionalneeds"] = booking.additionalneeds
    return payload
