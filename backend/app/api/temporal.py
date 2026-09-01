from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.clients.met import MetNorwayClient
from app.config import get_settings
from app.services.grid import cells_around
from app.services.spatial_temporal import SpatialTemporalService, SpatialWeatherUnavailable
from app.services.temporal import build_temporal_forecast

router = APIRouter()
settings = get_settings()
_spatial_service = SpatialTemporalService(
    MetNorwayClient(settings.met_user_agent, settings.met_timeout_seconds),
    cache_ttl_seconds=settings.met_spatial_cache_ttl_seconds,
    max_nodes=settings.met_spatial_max_nodes,
    concurrency=settings.met_spatial_concurrency,
)


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


@router.get("/temporal/cells")
async def spatial_temporal_forecast(
    lat: float = Query(58.735, ge=-90, le=90),
    lon: float = Query(5.647, ge=-180, le=180),
    radius_km: float = Query(3.0, gt=0, le=10),
    resolution: int | None = Query(None, ge=8, le=10),
    days: int = Query(10, ge=1, le=14),
    species: str = Query("Psilocybe semilanceata", min_length=2, max_length=120),
    max_weather_nodes: int | None = Query(None, ge=1, le=16),
) -> dict:
    h3_resolution = resolution or settings.default_h3_resolution
    cells = cells_around(lat, lon, radius_km, h3_resolution)
    if len(cells) > settings.live_cell_limit:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Requested {len(cells)} H3 cells; spatial live weather is capped at "
                f"{settings.live_cell_limit}. Reduce radius or H3 resolution."
            ),
        )

    node_limit = min(
        settings.met_spatial_max_nodes,
        max_weather_nodes or settings.met_spatial_max_nodes,
    )
    try:
        result = await _spatial_service.forecast_cells(
            cells,
            days=days,
            max_nodes=node_limit,
        )
    except SpatialWeatherUnavailable as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    result.update(
        {
            "species": species,
            "center": [lon, lat],
            "radius_km": radius_km,
            "h3_resolution": h3_resolution,
            "cell_count": len(cells),
            "species_specific_weather_model": False,
            "interpretation": (
                "Spatial weather varies by bounded MET sampling nodes. H3 cells inherit the nearest "
                "successful node forecast; habitat suitability remains a separate component."
            ),
        }
    )
    return result
