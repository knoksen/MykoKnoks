from __future__ import annotations

from datetime import datetime
from math import exp, log
from typing import Any


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _window_total(
    history: list[tuple[datetime, float]],
    now: datetime,
    hours: float,
) -> float:
    return sum(
        rain
        for timestamp, rain in history
        if 0.0 <= (now - timestamp).total_seconds() / 3600.0 <= hours
    )


def enrich_precipitation_memory(
    points: list[dict[str, Any]],
    *,
    half_life_hours: float = 48.0,
) -> list[dict[str, Any]]:
    """Attach an auditable rainfall-memory proxy to a chronological MET timeline.

    Memory is calculated only from precipitation represented inside the supplied
    timeline. It is therefore *not* a replacement for observed historical rainfall.
    The coverage field makes that warm-up limitation explicit.
    """
    if half_life_hours <= 0:
        raise ValueError("half_life_hours must be > 0")

    ordered = sorted(points, key=lambda item: str(item.get("time", "")))
    history: list[tuple[datetime, float]] = []
    decayed_rain_mm = 0.0
    previous_time: datetime | None = None
    first_time: datetime | None = None
    result: list[dict[str, Any]] = []

    decay_lambda = log(2.0) / half_life_hours
    for raw in ordered:
        if not raw.get("time"):
            continue
        timestamp = _parse_time(str(raw["time"]))
        if first_time is None:
            first_time = timestamp

        if previous_time is not None:
            delta_hours = max(0.0, (timestamp - previous_time).total_seconds() / 3600.0)
            decayed_rain_mm *= exp(-decay_lambda * delta_hours)

        rain = max(0.0, float(raw.get("precipitation_mm") or 0.0))
        decayed_rain_mm += rain
        history.append((timestamp, rain))
        history = [
            item
            for item in history
            if (timestamp - item[0]).total_seconds() / 3600.0 <= 168.0
        ]

        coverage_hours = 0.0 if first_time is None else max(
            0.0,
            (timestamp - first_time).total_seconds() / 3600.0,
        )
        memory_index = 1.0 - exp(-decayed_rain_mm / 12.0)

        enriched = dict(raw)
        enriched.update(
            {
                "antecedent_precip_24h_mm": round(_window_total(history, timestamp, 24.0), 2),
                "antecedent_precip_72h_mm": round(_window_total(history, timestamp, 72.0), 2),
                "antecedent_precip_168h_mm": round(_window_total(history, timestamp, 168.0), 2),
                "rain_memory_mm": round(decayed_rain_mm, 3),
                "moisture_memory_index": round(max(0.0, min(1.0, memory_index)), 4),
                "memory_coverage_hours": round(min(168.0, coverage_hours), 1),
                "memory_quality": "mature" if coverage_hours >= 72.0 else "warming_up",
            }
        )
        result.append(enriched)
        previous_time = timestamp

    return result
