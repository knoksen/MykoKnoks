from __future__ import annotations

import asyncio
from dataclasses import dataclass
from math import atan, cos, degrees, pi, sqrt

from app.clients.kartverket import KartverketElevationClient


@dataclass(frozen=True)
class TerrainMetrics:
    slope_deg: float
    roughness_m: float
    sample_spacing_m: float
    sample_count: int

    def as_dict(self) -> dict[str, float | int]:
        return {
            "slope_deg": round(self.slope_deg, 3),
            "roughness_m": round(self.roughness_m, 3),
            "sample_spacing_m": round(self.sample_spacing_m, 1),
            "sample_count": self.sample_count,
        }


def derive_terrain_metrics(
    center_m: float,
    north_m: float,
    south_m: float,
    east_m: float,
    west_m: float,
    *,
    spacing_m: float,
) -> TerrainMetrics:
    """Derive local gradient and elevation roughness from a five-point stencil."""
    if spacing_m <= 0:
        raise ValueError("spacing_m must be > 0")

    dz_dx = (east_m - west_m) / (2.0 * spacing_m)
    dz_dy = (north_m - south_m) / (2.0 * spacing_m)
    gradient = sqrt(dz_dx * dz_dx + dz_dy * dz_dy)
    slope = degrees(atan(gradient))

    values = [center_m, north_m, south_m, east_m, west_m]
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    roughness = sqrt(variance)

    return TerrainMetrics(
        slope_deg=max(0.0, min(90.0, slope)),
        roughness_m=max(0.0, roughness),
        sample_spacing_m=spacing_m,
        sample_count=len(values),
    )


async def sample_terrain_metrics(
    client: KartverketElevationClient,
    lat: float,
    lon: float,
    *,
    center_elevation_m: float,
    spacing_m: float = 50.0,
) -> TerrainMetrics:
    """Sample four offsets around a known centre elevation using Kartverket WPS."""
    lat_delta = spacing_m / 111_320.0
    lon_scale = max(0.15, cos(lat * pi / 180.0))
    lon_delta = spacing_m / (111_320.0 * lon_scale)

    north, south, east, west = await asyncio.gather(
        client.point(lat + lat_delta, lon),
        client.point(lat - lat_delta, lon),
        client.point(lat, lon + lon_delta),
        client.point(lat, lon - lon_delta),
    )
    values = [north.elevation_m, south.elevation_m, east.elevation_m, west.elevation_m]
    if any(value is None for value in values):
        raise ValueError("terrain metric sample returned missing elevation")

    return derive_terrain_metrics(
        center_elevation_m,
        float(north.elevation_m),
        float(south.elevation_m),
        float(east.elevation_m),
        float(west.elevation_m),
        spacing_m=spacing_m,
    )
