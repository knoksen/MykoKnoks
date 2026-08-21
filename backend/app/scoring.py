from dataclasses import dataclass
from math import exp


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def triangular(value: float, optimum: float, width: float) -> float:
    if width <= 0:
        raise ValueError("width must be > 0")
    return clamp01(1.0 - abs(value - optimum) / width)


@dataclass(frozen=True)
class HabitatFeatures:
    grassland: float
    forest_edge: float
    soil_moisture_proxy: float
    elevation_m: float


@dataclass(frozen=True)
class WeatherFeatures:
    temperature_c: float
    humidity_pct: float
    precipitation_1h_mm: float


def habitat_score(features: HabitatFeatures) -> tuple[float, list[str]]:
    elevation_penalty = exp(-max(0.0, features.elevation_m - 550.0) / 500.0)
    score = 0.40 * clamp01(features.grassland) + 0.20 * clamp01(features.forest_edge) + 0.30 * clamp01(features.soil_moisture_proxy) + 0.10 * elevation_penalty
    drivers = []
    if features.grassland > 0.65: drivers.append("grassland-like habitat")
    if features.soil_moisture_proxy > 0.65: drivers.append("moisture-supporting terrain")
    if features.forest_edge > 0.6: drivers.append("edge habitat")
    return clamp01(score), drivers


def fruiting_score(features: WeatherFeatures) -> tuple[float, list[str]]:
    temp = triangular(features.temperature_c, optimum=11.0, width=12.0)
    humidity = clamp01((features.humidity_pct - 45.0) / 50.0)
    rain = clamp01(features.precipitation_1h_mm / 3.0)
    score = 0.45 * temp + 0.35 * humidity + 0.20 * rain
    drivers = []
    if temp > 0.75: drivers.append("favourable temperature")
    if humidity > 0.7: drivers.append("high humidity")
    if rain > 0.35: drivers.append("recent/forecast precipitation")
    return clamp01(score), drivers


def combine_scores(habitat: float, fruiting: float) -> float:
    return clamp01(habitat * fruiting)
