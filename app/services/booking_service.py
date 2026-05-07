import httpx
from typing import Optional
from app.config import settings


class BookingService:
    def __init__(self):
        self.base_url = settings.booker_base_url
        self._token: Optional[str] = None

    async def _get_token(self) -> str:
        if self._token:
            return self._token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth",
                json={
                    "username": settings.booker_username,
                    "password": settings.booker_password,
                },
            )
            response.raise_for_status()
            self._token = response.json()["token"]
            return self._token

    async def _auth_headers(self) -> dict:
        token = await self._get_token()
        return {"Cookie": f"token={token}"}

    # ── Read ────────────────────────────────────────────────────────────────

    async def list_bookings(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/booking")
            response.raise_for_status()
            return response.json()

    async def get_booking(self, booking_id: int) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/booking/{booking_id}",
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            return response.json()

    # ── Create ──────────────────────────────────────────────────────────────

    async def create_booking(self, data: dict) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/booking",
                json=data,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            return response.json()

    # ── Update ──────────────────────────────────────────────────────────────

    async def update_booking(self, booking_id: int, data: dict) -> dict:
        headers = await self._auth_headers()
        headers["Accept"] = "application/json"

        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/booking/{booking_id}",
                json=data,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()

    async def partial_update_booking(self, booking_id: int, data: dict) -> dict:
        headers = await self._auth_headers()
        headers["Accept"] = "application/json"

        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.base_url}/booking/{booking_id}",
                json=data,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()

    # ── Delete ──────────────────────────────────────────────────────────────

    async def delete_booking(self, booking_id: int) -> bool:
        headers = await self._auth_headers()

        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/booking/{booking_id}",
                headers=headers,
            )
            return response.status_code == 201


booking_service = BookingService()
