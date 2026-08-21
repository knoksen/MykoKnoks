from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
import httpx

from app.clients.met import MetNorwayClient
from app.config import get_settings
from app.scoring import WeatherFeatures, combine_scores, fruiting_score, habitat_score
from app.services.grid import cell_geometry, cells_around, synthetic_habitat_features

router = APIRouter()
settings = get_settings()


@router.get("/meta")
def meta() -> dict:
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "status": "MVP",
        "default_h3_resolution": settings.default_h3_resolution,
        "model": "transparent heuristic baseline; production SDM not trained yet",
        "warning": "Predicted environmental suitability is not confirmed species presence or identification.",
    }


@router.get("/weather")
async def weather(lat: float = Query(ge=-90, le=90), lon: float = Query(ge=-180, le=180)) -> dict:
    client = MetNorwayClient(settings.met_user_agent, settings.met_timeout_seconds)
    try:
        result = await client.forecast(lat, lon)
        return result.model_dump()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"MET Norway upstream error: {exc}") from exc


@router.get("/cells")
async def cells(
    lat: float = Query(58.735, ge=-90, le=90),
    lon: float = Query(5.647, ge=-180, le=180),
    radius_km: float = Query(5.0, gt=0, le=25),
    species: str = Query("Psilocybe semilanceata", min_length=2, max_length=120),
    resolution: int | None = Query(None, ge=7, le=10),
) -> dict:
    resolution = resolution or settings.default_h3_resolution
    client = MetNorwayClient(settings.met_user_agent, settings.met_timeout_seconds)
    weather_source = "fallback demo weather"
    try:
        wx = await client.forecast(lat, lon)
        weather_features = WeatherFeatures(
            temperature_c=wx.air_temperature_c if wx.air_temperature_c is not None else 11.0,
            humidity_pct=wx.relative_humidity_pct if wx.relative_humidity_pct is not None else 80.0,
            precipitation_1h_mm=wx.precipitation_1h_mm or 0.0,
        )
        weather_source = wx.source
    except httpx.HTTPError:
        weather_features = WeatherFeatures(temperature_c=11.0, humidity_pct=80.0, precipitation_1h_mm=0.5)

    f_score, f_drivers = fruiting_score(weather_features)
    features = []
    for cell in cells_around(lat, lon, radius_km, resolution):
        h_features = synthetic_habitat_features(cell)
        h_score, h_drivers = habitat_score(h_features)
        features.append({
            "type": "Feature",
            "id": cell,
            "geometry": cell_geometry(cell),
            "properties": {
                "h3": cell,
                "species": species,
                "habitat": round(h_score, 4),
                "fruiting": round(f_score, 4),
                "combined": round(combine_scores(h_score, f_score), 4),
                "confidence": 0.30,
                "drivers": h_drivers + f_drivers,
                "synthetic_habitat": True,
            },
        })

    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "species": species,
            "center": [lon, lat],
            "radius_km": radius_km,
            "h3_resolution": resolution,
            "weather_source": weather_source,
            "habitat_source": "deterministic synthetic MVP placeholders",
        },
    }
