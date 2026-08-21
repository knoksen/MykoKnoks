from __future__ import annotations

import httpx


class ArtskartClient:
    """Adapter around Artsdatabanken's public Artskart output API."""
    BASE_URL = "https://artskart.artsdatabanken.no/publicapi/api"

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self.timeout_seconds = timeout_seconds

    async def observations(self, params: dict[str, str | int | float]) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(f"{self.BASE_URL}/Observations/list/", params=params)
            response.raise_for_status()
            return response.json()

    async def taxon_search(self, params: dict[str, str | int | float]) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(f"{self.BASE_URL}/taxon", params=params)
            response.raise_for_status()
            return response.json()
