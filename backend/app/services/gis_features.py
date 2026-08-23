from __future__ import annotations

import json
import re
from dataclasses import dataclass
from math import exp
from typing import Any

from app.scoring import HabitatFeatures, clamp01


@dataclass(frozen=True)
class NormalizedGISVector:
    ar5_code: int | None = None
    ar5_class: str | None = None
    open_land_score: float = 0.5
    wetland_score: float = 0.5
    forest_score: float = 0.5
    dominant_tree: str | None = None
    forest_height_m: float | None = None
    forest_height_raw: float | None = None
    loose_sediment_class: str | None = None
    substrate_moisture_score: float = 0.5
    slope_deg: float | None = None
    terrain_roughness_m: float | None = None
    coverage: float = 0.0
    evidence_sources: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "ar5_code": self.ar5_code,
            "ar5_class": self.ar5_class,
            "open_land_score": round(clamp01(self.open_land_score), 4),
            "wetland_score": round(clamp01(self.wetland_score), 4),
            "forest_score": round(clamp01(self.forest_score), 4),
            "dominant_tree": self.dominant_tree,
            "forest_height_m": self.forest_height_m,
            "forest_height_raw": self.forest_height_raw,
            "loose_sediment_class": self.loose_sediment_class,
            "substrate_moisture_score": round(clamp01(self.substrate_moisture_score), 4),
            "slope_deg": self.slope_deg,
            "terrain_roughness_m": self.terrain_roughness_m,
            "coverage": round(clamp01(self.coverage), 4),
            "evidence_sources": list(self.evidence_sources),
        }


def _payload_properties(payload: dict | str | None) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    if isinstance(payload.get("features"), list):
        for feature in payload["features"]:
            if isinstance(feature, dict) and isinstance(feature.get("properties"), dict):
                return feature["properties"]
    if isinstance(payload.get("properties"), dict):
        return payload["properties"]
    return payload


def _payload_text(payload: dict | str | None) -> str:
    if payload is None:
        return ""
    if isinstance(payload, str):
        return payload.casefold()
    return json.dumps(payload, ensure_ascii=False, default=str).casefold()


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"-?\d+(?:[.,]\d+)?", value)
        if match:
            try:
                return float(match.group(0).replace(",", "."))
            except ValueError:
                return None
    return None


def _value_for_keys(properties: dict[str, Any], terms: tuple[str, ...]) -> Any:
    for key, value in properties.items():
        folded = str(key).casefold()
        if any(term in folded for term in terms):
            return value
    return None


def _label_for_keys(properties: dict[str, Any], terms: tuple[str, ...]) -> str | None:
    value = _value_for_keys(properties, terms)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _ar5_features(payload: dict | str | None) -> tuple[int | None, str | None, float, float, float]:
    properties = _payload_properties(payload)
    text = _payload_text(payload)
    raw_code = _value_for_keys(properties, ("arealtype", "artype", "ar5type"))
    numeric = _number(raw_code)
    code = int(numeric) if numeric is not None and numeric.is_integer() else None
    label = _label_for_keys(properties, ("arealtype", "areal_type", "markslag", "beskrivelse"))

    open_land = 0.5
    wetland = 0.5
    forest = 0.5

    # AR5 main area-type codes. Text labels remain the preferred signal when supplied.
    if code in {21, 22, 23}:
        open_land, wetland, forest = 0.95, 0.2, 0.05
    elif code == 30:
        open_land, wetland, forest = 0.12, 0.3, 0.95
    elif code == 50:
        open_land, wetland, forest = 0.82, 0.25, 0.08
    elif code == 60:
        open_land, wetland, forest = 0.72, 0.98, 0.08
    elif code in {11, 12, 81, 82}:
        open_land, wetland, forest = 0.05, 0.2, 0.05

    if any(term in text for term in ("fulldyrka", "overflatedyrka", "innmarksbeite", "beite", "grass", "gras", "jordbruk")):
        open_land = max(open_land, 0.94)
        forest = min(forest, 0.08)
    if any(term in text for term in ("myr", "våtmark", "vatmark", "mire", "wetland")):
        wetland = max(wetland, 0.96)
        open_land = max(open_land, 0.65)
    if any(term in text for term in ("skog", "forest")):
        forest = max(forest, 0.94)
        open_land = min(open_land, 0.18)
    if any(term in text for term in ("bebyg", "samferd", "vann", "vatn", "hav")):
        open_land = min(open_land, 0.12)

    return code, label, clamp01(open_land), clamp01(wetland), clamp01(forest)


def _sr16_features(payload: dict | str | None) -> tuple[str | None, float | None, float | None]:
    properties = _payload_properties(payload)
    text = _payload_text(payload)
    tree = _label_for_keys(properties, ("treslag", "tree", "species"))
    raw_height = _value_for_keys(properties, ("hoyde", "høyde", "height", "srvhoyde"))
    height_raw = _number(raw_height)
    height_m = height_raw if height_raw is not None and 0 <= height_raw <= 80 else None

    if tree is None:
        for token, label in (("gran", "gran"), ("furu", "furu"), ("lauv", "lauv"), ("løv", "løv")):
            if token in text:
                tree = label
                break
    return tree, height_m, height_raw


def _ngu_features(payload: dict | str | None) -> tuple[str | None, float]:
    properties = _payload_properties(payload)
    text = _payload_text(payload)
    label = _label_for_keys(
        properties,
        ("losmasse", "løsmasse", "material", "jordart", "navn", "type"),
    )
    moisture = 0.5
    if any(term in text for term in ("torv", "myr", "peat", "flom", "elve", "marine", "havavset", "leire")):
        moisture = 0.82
    elif any(term in text for term in ("sand", "grus", "breelv", "morene")):
        moisture = 0.48
    elif any(term in text for term in ("bart fjell", "berg", "blokk", "ur")):
        moisture = 0.22
    return label, moisture


def normalize_gis_evidence(
    ar5: dict | str | None,
    sr16: dict | str | None,
    loose_sediment: dict | str | None,
    *,
    slope_deg: float | None = None,
    terrain_roughness_m: float | None = None,
) -> NormalizedGISVector:
    ar5_code, ar5_class, open_land, wetland, forest = _ar5_features(ar5)
    dominant_tree, forest_height_m, forest_height_raw = _sr16_features(sr16)
    sediment_class, substrate_moisture = _ngu_features(loose_sediment)

    sources: list[str] = []
    if ar5 is not None:
        sources.append("nibio_ar5")
    if sr16 is not None:
        sources.append("nibio_sr16")
    if loose_sediment is not None:
        sources.append("ngu_losmasse")
    if slope_deg is not None or terrain_roughness_m is not None:
        sources.append("kartverket_elevation_gradient")

    coverage = len(sources) / 4.0
    return NormalizedGISVector(
        ar5_code=ar5_code,
        ar5_class=ar5_class,
        open_land_score=open_land,
        wetland_score=wetland,
        forest_score=forest,
        dominant_tree=dominant_tree,
        forest_height_m=forest_height_m,
        forest_height_raw=forest_height_raw,
        loose_sediment_class=sediment_class,
        substrate_moisture_score=substrate_moisture,
        slope_deg=slope_deg,
        terrain_roughness_m=terrain_roughness_m,
        coverage=coverage,
        evidence_sources=tuple(sources),
    )


def prediction_habitat_score(
    species: str,
    habitat: HabitatFeatures,
    gis: dict[str, Any] | NormalizedGISVector | None,
) -> tuple[float, dict[str, float | str | None], list[str]]:
    from app.scoring import habitat_score

    legacy_score, legacy_drivers = habitat_score(habitat)
    if isinstance(gis, NormalizedGISVector):
        vector = gis.as_dict()
    else:
        vector = gis or {}

    coverage = clamp01(float(vector.get("coverage") or 0.0))
    species_key = species.strip().casefold()
    elevation_penalty = exp(-max(0.0, habitat.elevation_m - 550.0) / 500.0)

    if species_key != "psilocybe semilanceata" or coverage <= 0:
        return legacy_score, {
            "profile": "generic-legacy-v0.9",
            "legacy_habitat": round(legacy_score, 4),
            "gis_coverage": round(coverage, 4),
            "open_land": None,
            "substrate_moisture": None,
            "forest_edge": round(clamp01(habitat.forest_edge), 4),
            "elevation": round(clamp01(elevation_penalty), 4),
        }, legacy_drivers + (["GIS evidence retained as context; no taxon-specific v0.9 profile"] if coverage > 0 else [])

    open_land = clamp01(float(vector.get("open_land_score", habitat.grassland)))
    moisture = clamp01(float(vector.get("substrate_moisture_score", habitat.soil_moisture_proxy)))
    forest = clamp01(float(vector.get("forest_score", 0.5)))
    edge = clamp01(habitat.forest_edge)

    score = clamp01(
        0.46 * open_land
        + 0.24 * moisture
        + 0.12 * edge
        + 0.10 * clamp01(elevation_penalty)
        + 0.08 * (1.0 - forest)
    )
    drivers = list(legacy_drivers)
    drivers.append("v0.9 semilanceata GIS heuristic profile")
    if open_land >= 0.75:
        drivers.append("AR5/open-land evidence supports grassland habitat")
    if moisture >= 0.7:
        drivers.append("NGU substrate evidence supports moisture retention")
    if forest >= 0.75:
        drivers.append("strong forest signal reduces open-grassland suitability")

    return score, {
        "profile": "semilanceata-gis-heuristic-v0.9",
        "legacy_habitat": round(legacy_score, 4),
        "gis_coverage": round(coverage, 4),
        "open_land": round(open_land, 4),
        "substrate_moisture": round(moisture, 4),
        "forest_context": round(forest, 4),
        "forest_edge": round(edge, 4),
        "elevation": round(clamp01(elevation_penalty), 4),
    }, drivers
