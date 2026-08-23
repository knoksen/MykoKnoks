from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass

import httpx

from app.clients.kartverket import KartverketElevationClient
from app.clients.ogc import FeatureInfoResult, WmsClient
from app.config import Settings
from app.schemas import EnvironmentalSnapshot
from app.scoring import HabitatFeatures
from app.services.gis_features import normalize_gis_evidence
from app.services.terrain_metrics import sample_terrain_metrics


@dataclass(frozen=True)
class FeatureClients:
    elevation: KartverketElevationClient
    ar5: WmsClient
    sr16: WmsClient
    losmasse: WmsClient


def build_feature_clients(settings: Settings) -> FeatureClients:
    timeout = settings.upstream_timeout_seconds
    return FeatureClients(
        elevation=KartverketElevationClient(settings.kartverket_elevation_url, timeout),
        ar5=WmsClient(settings.nibio_ar5_wms_url, "nibio_ar5", timeout),
        sr16=WmsClient(settings.nibio_sr16_wms_url, "nibio_sr16", timeout),
        losmasse=WmsClient(settings.ngu_losmasse_wms_url, "ngu_losmasse", timeout),
    )


def _evidence_text(value: dict | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.casefold()
    return json.dumps(value, ensure_ascii=False, default=str).casefold()


def proxies_from_evidence(
    terrain: str | None,
    ar5: dict | str | None,
    sr16: dict | str | None,
    losmasse: dict | str | None,
) -> tuple[float, float, float, list[str]]:
    vector = normalize_gis_evidence(ar5, sr16, losmasse)
    text_land = " ".join(filter(None, [(terrain or "").casefold(), _evidence_text(ar5)]))
    drivers: list[str] = []

    grassland = vector.open_land_score
    if grassland > 0.8:
        drivers.append("real AR5 evidence supports open/grassland habitat")

    forest_edge = 0.5
    if sr16 is not None:
        forest_edge = 0.62
        drivers.append("SR16 forest evidence available")
    if any(term in text_land for term in ("skog", "forest")):
        forest_edge = max(forest_edge, 0.68)

    soil_moisture = vector.substrate_moisture_score
    if soil_moisture > 0.7:
        drivers.append("NGU substrate evidence suggests moisture retention")
    elif soil_moisture < 0.3:
        drivers.append("NGU substrate evidence suggests low moisture retention")

    if vector.wetland_score > 0.85:
        drivers.append("AR5 evidence indicates mire/wetland context")
    if vector.forest_score > 0.8:
        drivers.append("AR5 evidence indicates forest-dominated land cover")

    return grassland, forest_edge, soil_moisture, drivers


class LiveNorwayFeatureService:
    def __init__(self, settings: Settings, clients: FeatureClients | None = None) -> None:
        self.settings = settings
        self.clients = clients or build_feature_clients(settings)

    async def _wms_probe(
        self,
        client: WmsClient,
        lat: float,
        lon: float,
        terms: tuple[str, ...],
    ) -> FeatureInfoResult | None:
        layer = await client.find_layer(terms)
        if layer is None:
            return None
        return await client.feature_info(lat, lon, layer.name)

    async def probe(
        self,
        lat: float,
        lon: float,
        include_wms: bool = True,
        include_terrain_metrics: bool = False,
    ) -> EnvironmentalSnapshot:
        warnings: list[str] = []
        provenance: list[str] = []
        elevation = None
        terrain = None
        slope_deg = None
        terrain_roughness_m = None
        ar5_payload: dict | str | None = None
        sr16_payload: dict | str | None = None
        losmasse_payload: dict | str | None = None

        try:
            point = await self.clients.elevation.point(lat, lon)
            elevation = point.elevation_m
            terrain = point.terrain
            provenance.append("kartverket_elevation")
        except (httpx.HTTPError, ValueError) as exc:
            warnings.append(f"Kartverket elevation unavailable: {type(exc).__name__}")

        if include_terrain_metrics and elevation is not None:
            try:
                metrics = await sample_terrain_metrics(
                    self.clients.elevation,
                    lat,
                    lon,
                    center_elevation_m=float(elevation),
                )
                slope_deg = metrics.slope_deg
                terrain_roughness_m = metrics.roughness_m
                provenance.append("kartverket_elevation_gradient")
            except (httpx.HTTPError, ValueError) as exc:
                warnings.append(f"Kartverket terrain gradient unavailable: {type(exc).__name__}")

        if include_wms:
            probes = [
                self._wms_probe(self.clients.ar5, lat, lon, ("areal", "ar5", "markslag")),
                self._wms_probe(self.clients.sr16, lat, lon, ("treslag", "skogressurs", "sr16")),
                self._wms_probe(self.clients.losmasse, lat, lon, ("løsmasse", "losmasse", "flate")),
            ]
            results = await asyncio.gather(*probes, return_exceptions=True)
            for source_id, result in zip(
                ("nibio_ar5", "nibio_sr16", "ngu_losmasse"),
                results,
            ):
                if isinstance(result, BaseException):
                    warnings.append(f"{source_id} unavailable: {type(result).__name__}")
                    continue
                if result is None:
                    warnings.append(f"{source_id}: no queryable layer discovered")
                    continue
                provenance.append(source_id)
                if source_id == "nibio_ar5":
                    ar5_payload = result.payload
                elif source_id == "nibio_sr16":
                    sr16_payload = result.payload
                else:
                    losmasse_payload = result.payload

        normalized = normalize_gis_evidence(
            ar5_payload,
            sr16_payload,
            losmasse_payload,
            slope_deg=slope_deg,
            terrain_roughness_m=terrain_roughness_m,
        )
        grassland, forest_edge, soil_moisture, proxy_drivers = proxies_from_evidence(
            terrain,
            ar5_payload,
            sr16_payload,
            losmasse_payload,
        )
        available = sum(
            value is not None
            for value in (elevation, ar5_payload, sr16_payload, losmasse_payload)
        )
        completeness = available / 4.0
        provenance.extend(driver for driver in proxy_drivers if driver not in provenance)
        return EnvironmentalSnapshot(
            lat=lat,
            lon=lon,
            elevation_m=elevation,
            terrain=terrain,
            slope_deg=slope_deg,
            terrain_roughness_m=terrain_roughness_m,
            ar5_evidence=ar5_payload,
            sr16_evidence=sr16_payload,
            loose_sediment_evidence=losmasse_payload,
            grassland_proxy=grassland,
            forest_edge_proxy=forest_edge,
            soil_moisture_proxy=soil_moisture,
            normalized_gis=normalized.as_dict(),
            completeness=completeness,
            provenance=provenance,
            warnings=warnings,
        )

    @staticmethod
    def to_habitat_features(snapshot: EnvironmentalSnapshot) -> HabitatFeatures:
        return HabitatFeatures(
            grassland=snapshot.grassland_proxy,
            forest_edge=snapshot.forest_edge_proxy,
            soil_moisture_proxy=snapshot.soil_moisture_proxy,
            elevation_m=snapshot.elevation_m if snapshot.elevation_m is not None else 150.0,
        )
