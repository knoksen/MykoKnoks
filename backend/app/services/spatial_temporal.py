from __future__ import annotations

import asyncio
import math
import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.clients.met import MetNorwayClient
from app.services.grid import cell_center
from app.services.temporal import build_temporal_forecast


@dataclass(frozen=True)
class CachedForecast:
    expires_at: float
    forecast: dict[str, Any]


class SpatialWeatherUnavailable(RuntimeError):
    pass


def _distance_km(a: list[float], b: list[float]) -> float:
    lon1, lat1 = map(math.radians, a)
    lon2, lat2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    value = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0088 * 2 * math.asin(min(1.0, math.sqrt(value)))


def select_weather_nodes(cells: list[str], max_nodes: int) -> list[str]:
    """Deterministically choose spatially dispersed H3 cells as weather request nodes."""
    unique = sorted(set(cells))
    limit = max(1, max_nodes)
    if len(unique) <= limit:
        return unique

    centers = {cell: cell_center(cell) for cell in unique}
    mean_lon = sum(center[0] for center in centers.values()) / len(centers)
    mean_lat = sum(center[1] for center in centers.values()) / len(centers)
    centroid = [mean_lon, mean_lat]
    first = min(unique, key=lambda cell: (_distance_km(centers[cell], centroid), cell))
    selected = [first]

    while len(selected) < limit:
        remaining = [cell for cell in unique if cell not in selected]
        next_cell = max(
            remaining,
            key=lambda cell: (
                min(_distance_km(centers[cell], centers[node]) for node in selected),
                cell,
            ),
        )
        selected.append(next_cell)
    return selected


def _quality_label(coverage_ratio: float, max_assignment_distance_km: float) -> str:
    if coverage_ratio >= 0.99 and max_assignment_distance_km <= 3.0:
        return "high"
    if coverage_ratio >= 0.8 and max_assignment_distance_km <= 8.0:
        return "moderate"
    return "limited"


class SpatialTemporalService:
    """Bounded, cached MET sampling for spatially varying H3 temporal forecasts."""

    def __init__(
        self,
        client: MetNorwayClient,
        *,
        cache_ttl_seconds: float = 900.0,
        max_nodes: int = 9,
        concurrency: int = 4,
    ) -> None:
        self.client = client
        self.cache_ttl_seconds = max(1.0, cache_ttl_seconds)
        self.max_nodes = max(1, max_nodes)
        self.concurrency = max(1, concurrency)
        self._cache: dict[tuple[str, int], CachedForecast] = {}
        self._cache_lock = asyncio.Lock()

    async def _forecast_for_node(self, cell: str, days: int) -> tuple[dict[str, Any], bool]:
        key = (cell, days)
        now = time.monotonic()
        async with self._cache_lock:
            cached = self._cache.get(key)
            if cached and cached.expires_at > now:
                return cached.forecast, True

        lon, lat = cell_center(cell)
        payload = await self.client.raw_forecast(lat, lon)
        forecast = build_temporal_forecast(payload, days=days)
        async with self._cache_lock:
            self._cache[key] = CachedForecast(
                expires_at=time.monotonic() + self.cache_ttl_seconds,
                forecast=forecast,
            )
        return forecast, False

    async def forecast_cells(
        self,
        cells: list[str],
        *,
        days: int,
        max_nodes: int | None = None,
    ) -> dict[str, Any]:
        unique_cells = sorted(set(cells))
        if not unique_cells:
            return {
                "weather_nodes": [],
                "cells": [],
                "data_quality": {
                    "label": "limited",
                    "weather_node_coverage_ratio": 0.0,
                    "max_assignment_distance_km": None,
                },
            }

        requested_nodes = select_weather_nodes(
            unique_cells,
            min(self.max_nodes, max_nodes or self.max_nodes),
        )
        semaphore = asyncio.Semaphore(self.concurrency)

        async def load(cell: str) -> dict[str, Any]:
            async with semaphore:
                try:
                    forecast, cached = await self._forecast_for_node(cell, days)
                    return {
                        "h3": cell,
                        "center": cell_center(cell),
                        "forecast": forecast,
                        "cached": cached,
                        "error": None,
                    }
                except httpx.HTTPError as exc:
                    return {
                        "h3": cell,
                        "center": cell_center(cell),
                        "forecast": None,
                        "cached": False,
                        "error": f"{type(exc).__name__}: {exc}",
                    }

        node_results = await asyncio.gather(*(load(cell) for cell in requested_nodes))
        successful = [item for item in node_results if item["forecast"] is not None]
        if not successful:
            raise SpatialWeatherUnavailable("All bounded MET weather-node requests failed.")

        assignments: list[dict[str, Any]] = []
        distances: list[float] = []
        for cell in unique_cells:
            center = cell_center(cell)
            nearest = min(
                successful,
                key=lambda item: _distance_km(center, item["center"]),
            )
            distance = _distance_km(center, nearest["center"])
            distances.append(distance)
            assignments.append(
                {
                    "h3": cell,
                    "center": center,
                    "weather_node_h3": nearest["h3"],
                    "weather_node_distance_km": round(distance, 3),
                }
            )

        coverage_ratio = len(successful) / len(requested_nodes)
        max_distance = max(distances) if distances else 0.0
        return {
            "sampling": {
                "method": "deterministic farthest-point H3 weather nodes",
                "assignment": "nearest successful weather node",
                "requested_weather_nodes": len(requested_nodes),
                "successful_weather_nodes": len(successful),
                "concurrency_limit": self.concurrency,
                "cache_ttl_seconds": self.cache_ttl_seconds,
            },
            "weather_nodes": node_results,
            "cells": assignments,
            "data_quality": {
                "label": _quality_label(coverage_ratio, max_distance),
                "weather_node_coverage_ratio": round(coverage_ratio, 4),
                "max_assignment_distance_km": round(max_distance, 3),
                "meaning": (
                    "Data quality describes upstream-node coverage and spatial assignment distance; "
                    "it is not statistical model confidence."
                ),
            },
            "scientific_guardrail": (
                "Spatial variation comes from sampled MET forecast nodes. Assigned cells inherit "
                "the nearest successful node forecast; this is not per-cell observed weather."
            ),
        }
