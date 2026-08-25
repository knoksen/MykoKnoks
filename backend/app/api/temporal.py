from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.clients.met import MetNorwayClient
from app.config import get_settings
from app.services.temporal import build_temporal_forecast

router = APIRouter()
settings = get_settings()


@router.get("/temporal")
async def temporal_forecast(
    lat: float = Query(58.735, ge=-90, le=90),
    lon: float = Query(5.647, ge=-180, le=180),
    days: int = Query(10, ge=1, le=14),
    species: str = Query("Psilocybe semilanceata", min_length=2, max_length=120),
) -> dict:
    client = MetNorwayClient(settings.met_user_agent, settings.met_timeout_seconds)
    try:
        payload = await client.raw_forecast(lat, lon)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"MET Norway upstream error: {exc}") from exc

    result = build_temporal_forecast(payload, days=days)
    result["species"] = species
    result["center"] = [lon, lat]
    result["species_specific_weather_model"] = False
    result["interpretation"] = (
        "Weather-driven timing with transparent precipitation memory. Memory is computed "
        "inside the available MET timeline and does not claim observed pre-forecast history."
    )
    return result
