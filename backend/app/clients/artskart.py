from __future__ import annotations

from math import log, pi, radians, tan

import httpx


def lonlat_to_web_mercator(lon: float, lat: float) -> tuple[float, float]:
    x = lon * 20037508.34 / 180.0
    clamped_lat = max(-85.05112878, min(85.05112878, lat))
    y = log(tan((90.0 + clamped_lat) * pi / 360.0)) / radians(1.0)
    y = y * 20037508.34 / 180.0
    return x, y


def web_mercator_bbox_wkt(lat: float, lon: float, radius_m: float) -> str:
    x, y = lonlat_to_web_mercator(lon, lat)
    left, right = x - radius_m, x + radius_m
    bottom, top = y - radius_m, y + radius_m
    return (
        "POLYGON(("
        f"{left} {bottom},{right} {bottom},{right} {top},{left} {top},{left} {bottom}"
        "))"
    )


class ArtskartClient:
    """Adapter around Artsdatabanken's public Artskart output API."""

    BASE_URL = "https://artskart.artsdatabanken.no/publicapi/api"

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self.timeout_seconds = timeout_seconds

    async def observations(self, params: dict[str, str | int | float]) -> dict | list:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(f"{self.BASE_URL}/Observations/list/", params=params)
            response.raise_for_status()
            return response.json()

    async def nearby(self, lat: float, lon: float, radius_m: float, page_size: int = 128) -> dict | list:
        params: dict[str, str | int | float] = {
            "gmWktPolygon": web_mercator_bbox_wkt(lat, lon, radius_m),
            "pageSize": page_size,
            "page": 0,
        }
        return await self.observations(params)

    async def taxon_search(self, term: str, page_size: int = 20) -> dict | list:
        params: dict[str, str | int | float] = {"term": term, "pageSize": page_size, "page": 0}
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(f"{self.BASE_URL}/taxon", params=params)
            response.raise_for_status()
            return response.json()
