from typing import Any

from pydantic import BaseModel, Field


class WeatherSnapshot(BaseModel):
    air_temperature_c: float | None = None
    relative_humidity_pct: float | None = None
    precipitation_1h_mm: float | None = None
    wind_speed_mps: float | None = None
    source: str
    time: str | None = None


class TerrainSnapshot(BaseModel):
    elevation_m: float | None = None
    terrain: str | None = None
    placenames: list[str] = Field(default_factory=list)
    source: str = "Kartverket elevation WPS"


class SourceDescriptor(BaseModel):
    id: str
    name: str
    organisation: str
    kind: str
    endpoint: str
    role: str
    live: bool = True
    license: str | None = None


class WmsLayer(BaseModel):
    name: str
    title: str
    queryable: bool = False


class EnvironmentalSnapshot(BaseModel):
    lat: float
    lon: float
    elevation_m: float | None = None
    terrain: str | None = None
    ar5_evidence: dict | str | None = None
    sr16_evidence: dict | str | None = None
    loose_sediment_evidence: dict | str | None = None
    grassland_proxy: float = Field(ge=0, le=1)
    forest_edge_proxy: float = Field(ge=0, le=1)
    soil_moisture_proxy: float = Field(ge=0, le=1)
    normalized_gis: dict[str, Any] = Field(default_factory=dict)
    completeness: float = Field(ge=0, le=1)
    provenance: list[str]
    warnings: list[str] = Field(default_factory=list)


class ScoreBreakdown(BaseModel):
    habitat: float = Field(ge=0, le=1)
    fruiting: float = Field(ge=0, le=1)
    combined: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    drivers: list[str]


class ForecastCell(BaseModel):
    h3: str
    species: str
    center: list[float]
    geometry: dict
    score: ScoreBreakdown


class CellCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list[dict]
    metadata: dict
