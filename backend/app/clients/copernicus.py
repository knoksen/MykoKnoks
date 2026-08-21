from __future__ import annotations

import httpx


class CopernicusStacClient:
    SEARCH_URL = "https://stac.dataspace.copernicus.eu/v1/search"

    async def search_sentinel2_l2a(self, bbox: tuple[float, float, float, float], datetime_range: str, max_cloud_cover: float = 20, limit: int = 20) -> dict:
        body = {
            "collections": ["sentinel-2-l2a"],
            "bbox": list(bbox),
            "datetime": datetime_range,
            "query": {"eo:cloud_cover": {"lt": max_cloud_cover}},
            "limit": limit,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.SEARCH_URL, json=body)
            response.raise_for_status()
            return response.json()
