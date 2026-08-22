from __future__ import annotations

import httpx

from app.schemas import WeatherSnapshot


class MetNorwayClient:
    BASE_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"

    def __init__(self, user_agent: str, timeout_seconds: float = 10.0) -> None:
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds

    async def raw_forecast(self, lat: float, lon: float) -> dict:
        params = {"lat": round(lat, 4), "lon": round(lon, 4)}
        headers = {"User-Agent": self.user_agent}
        async with httpx.AsyncClient(timeout=self.timeout_seconds, headers=headers) as client:
            response = await client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return response.json()

    async def forecast(self, lat: float, lon: float) -> WeatherSnapshot:
        payload = await self.raw_forecast(lat, lon)
        series = payload["properties"]["timeseries"][0]
        instant = series["data"]["instant"]["details"]
        next_1h = series["data"].get("next_1_hours", {}).get("details", {})
        return WeatherSnapshot(
            air_temperature_c=instant.get("air_temperature"),
            relative_humidity_pct=instant.get("relative_humidity"),
            precipitation_1h_mm=next_1h.get("precipitation_amount", 0.0),
            wind_speed_mps=instant.get("wind_speed"),
            source="MET Norway Locationforecast 2.0",
            time=series.get("time"),
        )
