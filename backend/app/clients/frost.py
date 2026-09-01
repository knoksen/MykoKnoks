from __future__ import annotations

from datetime import date
from typing import Any

import httpx


class FrostNotConfigured(RuntimeError):
    pass


class FrostClient:
    SOURCES_URL = "https://frost.met.no/sources/v0.jsonld"
    OBSERVATIONS_URL = "https://frost.met.no/observations/v0.jsonld"
    DAILY_PRECIPITATION_ELEMENT = "sum(precipitation_amount P1D)"

    def __init__(self, client_id: str | None, timeout_seconds: float = 15.0) -> None:
        self.client_id = (client_id or "").strip() or None
        self.timeout_seconds = timeout_seconds

    def _auth(self) -> httpx.BasicAuth:
        if not self.client_id:
            raise FrostNotConfigured("FROST_CLIENT_ID is not configured.")
        return httpx.BasicAuth(self.client_id, "")

    async def nearest_precipitation_sources(
        self,
        lat: float,
        lon: float,
        *,
        max_count: int = 3,
    ) -> list[dict[str, Any]]:
        params = {
            "types": "SensorSystem",
            "elements": self.DAILY_PRECIPITATION_ELEMENT,
            "geometry": f"nearest(POINT({lon:.6f} {lat:.6f}))",
            "nearestmaxcount": max(1, min(10, max_count)),
            "validtime": "now",
        }
        async with httpx.AsyncClient(timeout=self.timeout_seconds, auth=self._auth()) as client:
            response = await client.get(self.SOURCES_URL, params=params)
            response.raise_for_status()
            payload = response.json()
        data = payload.get("data", []) if isinstance(payload, dict) else []
        return [item for item in data if isinstance(item, dict)]

    async def daily_precipitation(
        self,
        sources: list[str],
        *,
        start: date,
        end: date,
        qualities: str = "0,1,2,3,4",
    ) -> list[dict[str, Any]]:
        if not sources:
            return []
        params = {
            "sources": ",".join(sources),
            "referencetime": f"{start.isoformat()}/{end.isoformat()}",
            "elements": self.DAILY_PRECIPITATION_ELEMENT,
            "levels": "default",
            "timeoffsets": "default",
            "qualities": qualities,
        }
        async with httpx.AsyncClient(timeout=self.timeout_seconds, auth=self._auth()) as client:
            response = await client.get(self.OBSERVATIONS_URL, params=params)
            response.raise_for_status()
            payload = response.json()
        data = payload.get("data", []) if isinstance(payload, dict) else []
        return [item for item in data if isinstance(item, dict)]
