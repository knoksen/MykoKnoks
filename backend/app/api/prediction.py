from __future__ import annotations

from typing import Literal

import httpx
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError

from app.clients.artskart import ArtskartClient
from app.clients.met import MetNorwayClient
from app.config import get_settings
from app.repositories.feature_store import FeatureStoreRepository
from app.scoring import WeatherFeatures, combine_scores, fruiting_score
from app.services.features import LiveNorwayFeatureService
from app.services.gis_features import prediction_habitat_score
from app.services.grid import cell_geometry, cells_around, synthetic_habitat_features
from app.services.live_grid import probe_cells
from app.services.occurrence import occurrence_context

router = APIRouter()
settings = get_settings()


def _feature_store_backend() -> str:
    scheme = settings.database_url.split(":", 1)[0]
    return scheme.split("+", 1)[0]


def _empty_gis() -> dict:
    return {
        "ar5_code": None,
        "ar5_class": None,
        "open_land_score": 0.5,
        "wetland_score": 0.5,
        "forest_score": 0.5,
        "dominant_tree": None,
        "forest_height_m": None,
        "forest_height_raw": None,
        "loose_sediment_class": None,
        "substrate_moisture_score": 0.5,
        "slope_deg": None,
        "terrain_roughness_m": None,
        "coverage": 0.0,
        "evidence_sources": [],
    }


def _gis_driver_summary(gis: dict) -> list[str]:
    drivers: list[str] = []
    if gis.get("ar5_class"):
        drivers.append(f"AR5 class: {gis['ar5_class']}")
    elif gis.get("ar5_code") is not None:
        drivers.append(f"AR5 code: {gis['ar5_code']}")
    if gis.get("dominant_tree"):
        drivers.append(f"SR16 tree context: {gis['dominant_tree']}")
    if gis.get("forest_height_m") is not None:
        drivers.append(f"SR16 forest height: {float(gis['forest_height_m']):.1f} m")
    if gis.get("loose_sediment_class"):
        drivers.append(f"NGU substrate: {gis['loose_sediment_class']}")
    if gis.get("slope_deg") is not None:
        drivers.append(f"terrain slope: {float(gis['slope_deg']):.1f}°")
    if gis.get("terrain_roughness_m") is not None:
        drivers.append(f"terrain roughness: {float(gis['terrain_roughness_m']):.1f} m")
    return drivers


@router.get("/prediction/cells")
async def prediction_cells(
    lat: float = Query(58.735, ge=-90, le=90),
    lon: float = Query(5.647, ge=-180, le=180),
    radius_km: float = Query(3.0, gt=0, le=25),
    species: str = Query("Psilocybe semilanceata", min_length=2, max_length=120),
    resolution: int | None = Query(None, ge=7, le=10),
    data_mode: Literal["demo", "live", "store"] = Query("demo"),
    include_occurrences: bool = Query(True),
    detailed_live_gis: bool = Query(False),
) -> dict:
    """Return H3 prediction cells with explicit GIS vectors and decomposition.

    Scores remain ecological indices, not calibrated occurrence probabilities. Detailed
    live GIS probing is opt-in and tightly capped to protect upstream public services.
    """
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
    if data_mode == "live" and detailed_live_gis and len(requested_cells) > 12:
        raise HTTPException(
            status_code=422,
            detail="Detailed live GIS is capped at 12 H3 cells. Use the persisted H3 store for larger areas.",
        )

    weather_client = MetNorwayClient(settings.met_user_agent, settings.met_timeout_seconds)
    weather_source = "fallback demo weather"
    weather_warning: str | None = None
    try:
        wx = await weather_client.forecast(lat, lon)
        weather_features = WeatherFeatures(
            temperature_c=wx.air_temperature_c if wx.air_temperature_c is not None else 11.0,
            humidity_pct=wx.relative_humidity_pct if wx.relative_humidity_pct is not None else 80.0,
            precipitation_1h_mm=wx.precipitation_1h_mm or 0.0,
        )
        weather_source = wx.source
    except httpx.HTTPError as exc:
        weather_features = WeatherFeatures(
            temperature_c=11.0,
            humidity_pct=80.0,
            precipitation_1h_mm=0.5,
        )
        weather_warning = f"MET Norway unavailable: {type(exc).__name__}; fallback weather used"

    f_score, f_drivers = fruiting_score(weather_features)

    occurrence = None
    occurrence_warning: str | None = None
    if include_occurrences and data_mode != "demo":
        try:
            payload = await ArtskartClient(settings.upstream_timeout_seconds).nearby(
                lat,
                lon,
                min(5000.0, max(500.0, radius_km * 1000.0)),
                128,
            )
            occurrence = occurrence_context(payload, species).as_dict()
        except httpx.HTTPError as exc:
            occurrence_warning = f"Artskart context unavailable: {type(exc).__name__}"

    live_snapshots = {}
    stored_features = {}
    store_error: str | None = None
    if data_mode == "live":
        service = LiveNorwayFeatureService(settings)
        live_snapshots = await probe_cells(
            requested_cells,
            service,
            settings.live_feature_concurrency,
            include_wms=detailed_live_gis,
            include_terrain_metrics=detailed_live_gis,
        )
    elif data_mode == "store":
        try:
            stored_features = FeatureStoreRepository(settings.database_url).get_many(requested_cells)
        except SQLAlchemyError as exc:
            store_error = type(exc).__name__

    features = []
    store_hits = 0
    profile_counts: dict[str, int] = {}
    for cell in requested_cells:
        terrain = None
        gis = _empty_gis()
        if data_mode == "live":
            snapshot = live_snapshots[cell]
            h_features = LiveNorwayFeatureService.to_habitat_features(snapshot)
            completeness = snapshot.completeness
            provenance = snapshot.provenance or ["live_probe_failed"]
            source_warnings = list(snapshot.warnings)
            synthetic = snapshot.completeness <= 0.0
            terrain = snapshot.terrain
            if snapshot.normalized_gis:
                gis = snapshot.normalized_gis
        elif data_mode == "store" and cell in stored_features:
            stored = stored_features[cell]
            h_features = stored.habitat
            completeness = stored.completeness
            provenance = stored.provenance
            source_warnings = []
            synthetic = False
            terrain = stored.terrain
            gis = stored.gis_features or _empty_gis()
            if stored.gis_features is None:
                source_warnings.append("stored cell predates normalized GIS feature vectors")
            store_hits += 1
        else:
            h_features = synthetic_habitat_features(cell)
            completeness = 0.0
            provenance = ["synthetic_demo" if data_mode == "demo" else "feature_store_miss"]
            source_warnings = [] if store_error is None else [f"feature store unavailable: {store_error}"]
            synthetic = True

        h_score, score_components, h_drivers = prediction_habitat_score(species, h_features, gis)
        profile = str(score_components.get("profile") or "unknown")
        profile_counts[profile] = profile_counts.get(profile, 0) + 1
        gis_coverage = float(gis.get("coverage") or 0.0)
        confidence = 0.25 if synthetic else min(
            0.90,
            0.34 + 0.44 * completeness + 0.12 * gis_coverage,
        )
        warnings = list(source_warnings)
        if weather_warning:
            warnings.append(weather_warning)

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
                    "drivers": h_drivers + _gis_driver_summary(gis) + f_drivers,
                    "score_components": score_components,
                    "model_profile": profile,
                    "gis_features": gis,
                    "synthetic_habitat": synthetic,
                    "data_mode": data_mode,
                    "provenance": provenance,
                    "source_warnings": warnings,
                    "elevation_m": h_features.elevation_m,
                    "terrain": terrain,
                },
            }
        )

    backend = _feature_store_backend()
    metadata_warnings = [value for value in (weather_warning, occurrence_warning) if value]
    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "engine": "model-platform-v1.0",
            "model_registry_id": "semilanceata-gis-heuristic-v1"
            if species.strip().casefold() == "psilocybe semilanceata"
            else "generic-legacy-v1",
            "model_semantics": (
                "explainable ecological suitability; not calibrated occurrence probability"
            ),
            "species": species,
            "center": [lon, lat],
            "radius_km": radius_km,
            "h3_resolution": resolution,
            "data_mode": data_mode,
            "detailed_live_gis": detailed_live_gis,
            "weather_source": weather_source,
            "feature_store_backend": backend if data_mode == "store" else None,
            "feature_store_hits": store_hits,
            "feature_store_total": len(requested_cells) if data_mode == "store" else None,
            "feature_store_error": store_error,
            "profile_counts": profile_counts,
            "occurrence_context": occurrence,
            "warnings": metadata_warnings,
            "guardrail": (
                "No nearby Artskart match is not absence evidence. Presence-only occurrence "
                "context does not automatically alter the cell score."
            ),
            "next_stage": (
                "populate national H3 store, build occurrence/background training matrix, "
                "run grouped spatial CV, then calibrate independently"
            ),
        },
    }
