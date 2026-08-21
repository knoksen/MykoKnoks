from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query
import httpx
from sqlalchemy.exc import SQLAlchemyError

from app.clients.artskart import ArtskartClient
from app.clients.met import MetNorwayClient
from app.clients.ogc import WmsClient
from app.config import get_settings
from app.repositories.feature_store import FeatureStoreRepository
from app.scoring import WeatherFeatures, combine_scores, fruiting_score, habitat_score
from app.services.features import LiveNorwayFeatureService
from app.services.grid import cell_geometry, cells_around, synthetic_habitat_features
from app.services.live_grid import probe_cells
from app.services.sources import source_catalog

router = APIRouter()
settings = get_settings()


@router.get("/meta")
def meta() -> dict:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "v0.2 real-data engine",
        "default_h3_resolution": settings.default_h3_resolution,
        "model": "explainable ecological evidence baseline; SDM training pipeline next",
        "data_modes": ["demo", "live", "store"],
        "warning": (
            "Environmental suitability is not confirmed species presence, edibility, "
            "or species identification."
        ),
    }


@router.get("/sources")
def sources() -> list[dict]:
    return [item.model_dump() for item in source_catalog(settings)]


@router.get("/sources/{source_id}/layers")
async def source_layers(source_id: str) -> list[dict]:
    urls = {
        "nibio_ar5": settings.nibio_ar5_wms_url,
        "nibio_sr16": settings.nibio_sr16_wms_url,
        "ngu_losmasse": settings.ngu_losmasse_wms_url,
    }
    if source_id not in urls:
        raise HTTPException(status_code=404, detail="Source does not expose WMS layer discovery")
    client = WmsClient(urls[source_id], source_id, settings.upstream_timeout_seconds)
    try:
        return [layer.model_dump() for layer in await client.capabilities()]
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream WMS error: {exc}") from exc


@router.get("/features/probe")
async def feature_probe(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    include_wms: bool = True,
) -> dict:
    service = LiveNorwayFeatureService(settings)
    snapshot = await service.probe(lat, lon, include_wms=include_wms)
    return snapshot.model_dump()


@router.get("/taxa/search")
async def taxon_search(
    term: str = Query(min_length=2, max_length=120),
    page_size: int = Query(20, ge=1, le=128),
) -> dict | list:
    client = ArtskartClient(settings.upstream_timeout_seconds)
    try:
        return await client.taxon_search(term, page_size)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Artskart upstream error: {exc}") from exc


@router.get("/observations/nearby")
async def observations_nearby(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    radius_m: float = Query(1000, gt=0, le=10000),
    page_size: int = Query(128, ge=1, le=128),
) -> dict | list:
    client = ArtskartClient(settings.upstream_timeout_seconds)
    try:
        return await client.nearby(lat, lon, radius_m, page_size)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Artskart upstream error: {exc}") from exc


@router.get("/weather")
async def weather(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
) -> dict:
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
    radius_km: float = Query(3.0, gt=0, le=25),
    species: str = Query("Psilocybe semilanceata", min_length=2, max_length=120),
    resolution: int | None = Query(None, ge=7, le=10),
    data_mode: Literal["demo", "live", "store"] = Query("demo"),
) -> dict:
    resolution = resolution or settings.default_h3_resolution
    requested_cells = cells_around(lat, lon, radius_km, resolution)
    if data_mode == "live" and len(requested_cells) > settings.live_cell_limit:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Live mode would query {len(requested_cells)} cells; limit is "
                f"{settings.live_cell_limit}. Reduce radius or H3 resolution."
            ),
        )

    weather_client = MetNorwayClient(settings.met_user_agent, settings.met_timeout_seconds)
    weather_source = "fallback demo weather"
    try:
        wx = await weather_client.forecast(lat, lon)
        weather_features = WeatherFeatures(
            temperature_c=wx.air_temperature_c if wx.air_temperature_c is not None else 11.0,
            humidity_pct=wx.relative_humidity_pct if wx.relative_humidity_pct is not None else 80.0,
            precipitation_1h_mm=wx.precipitation_1h_mm or 0.0,
        )
        weather_source = wx.source
    except httpx.HTTPError:
        weather_features = WeatherFeatures(
            temperature_c=11.0,
            humidity_pct=80.0,
            precipitation_1h_mm=0.5,
        )

    f_score, f_drivers = fruiting_score(weather_features)
    live_snapshots = {}
    stored_features = {}
    store_error: str | None = None

    if data_mode == "live":
        service = LiveNorwayFeatureService(settings)
        live_snapshots = await probe_cells(
            requested_cells,
            service,
            settings.live_feature_concurrency,
        )
    elif data_mode == "store":
        try:
            stored_features = FeatureStoreRepository(settings.database_url).get_many(requested_cells)
        except SQLAlchemyError as exc:
            store_error = type(exc).__name__

    features = []
    store_hits = 0
    for cell in requested_cells:
        terrain = None
        if data_mode == "live":
            snapshot = live_snapshots[cell]
            h_features = LiveNorwayFeatureService.to_habitat_features(snapshot)
            completeness = snapshot.completeness
            provenance = snapshot.provenance or ["live_probe_failed"]
            source_warnings = snapshot.warnings
            synthetic = snapshot.completeness <= 0.0
            terrain = snapshot.terrain
        elif data_mode == "store" and cell in stored_features:
            stored = stored_features[cell]
            h_features = stored.habitat
            completeness = stored.completeness
            provenance = stored.provenance
            source_warnings = []
            synthetic = False
            terrain = stored.terrain
            store_hits += 1
        else:
            h_features = synthetic_habitat_features(cell)
            completeness = 0.0
            provenance = ["synthetic_demo" if data_mode == "demo" else "feature_store_miss"]
            source_warnings = [] if store_error is None else [f"feature store unavailable: {store_error}"]
            synthetic = True

        h_score, h_drivers = habitat_score(h_features)
        confidence = 0.25 if synthetic else min(0.82, 0.35 + 0.47 * completeness)
        features.append(
            {
                "type": "Feature",
                "id": cell,
                "geometry": cell_geometry(cell),
                "properties": {
                    "h3": cell,
                    "species": species,
                    "habitat": round(h_score, 4),
                    "fruiting": round(f_score, 4),
                    "combined": round(combine_scores(h_score, f_score), 4),
                    "confidence": round(confidence, 4),
                    "drivers": h_drivers + f_drivers,
                    "synthetic_habitat": synthetic,
                    "data_mode": data_mode,
                    "provenance": provenance,
                    "source_warnings": source_warnings,
                    "elevation_m": h_features.elevation_m,
                    "terrain": terrain,
                },
            }
        )

    habitat_source = {
        "demo": "deterministic synthetic demo placeholders",
        "live": "Kartverket live elevation/terrain evidence",
        "store": "PostGIS H3 feature store with transparent fallback on cache miss",
    }[data_mode]
    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "species": species,
            "center": [lon, lat],
            "radius_km": radius_km,
            "h3_resolution": resolution,
            "data_mode": data_mode,
            "weather_source": weather_source,
            "habitat_source": habitat_source,
            "feature_store_hits": store_hits,
            "feature_store_total": len(requested_cells) if data_mode == "store" else None,
            "feature_store_error": store_error,
            "next_stage": "bulk AR5/SR16/NGU/Sentinel-2 normalization + trained SDM",
        },
    }
