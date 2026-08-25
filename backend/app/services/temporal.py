from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from app.scoring import WeatherFeatures, clamp01, fruiting_score
from app.services.weather_memory import enrich_precipitation_memory


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)


def _precipitation(data: dict[str, Any]) -> tuple[float, int]:
    for key, hours in (("next_1_hours", 1), ("next_6_hours", 6), ("next_12_hours", 12)):
        details = data.get(key, {}).get("details", {})
        amount = details.get("precipitation_amount")
        if amount is not None:
            return max(0.0, float(amount)), hours
    return 0.0, 1


def build_temporal_forecast(payload: dict[str, Any], days: int = 10) -> dict[str, Any]:
    """Convert MET Locationforecast timeseries to an auditable fruiting timeline.

    v1.0 adds a decaying precipitation-memory proxy. The memory is built from the
    supplied forecast timeline and therefore does not pretend to be observed rainfall
    before the first available timestamp.
    """
    raw_series = payload.get("properties", {}).get("timeseries", [])
    if not raw_series:
        return {
            "source": "MET Norway Locationforecast 2.0",
            "points": [],
            "days": [],
            "best_day": None,
            "model": "weather-memory fruiting heuristic v1.0",
            "warning": "No MET forecast timeseries returned.",
        }

    first_time = _parse_time(raw_series[0]["time"])
    cutoff = first_time + timedelta(days=max(1, min(days, 14)))
    base_points: list[dict[str, Any]] = []

    for series in raw_series:
        time_text = series.get("time")
        if not time_text:
            continue
        timestamp = _parse_time(time_text)
        if timestamp >= cutoff:
            break

        data = series.get("data", {})
        instant = data.get("instant", {}).get("details", {})
        temperature = instant.get("air_temperature")
        humidity = instant.get("relative_humidity")
        wind = instant.get("wind_speed")
        if temperature is None or humidity is None:
            continue

        precipitation_mm, precipitation_window_hours = _precipitation(data)
        precipitation_rate = precipitation_mm / max(1, precipitation_window_hours)
        score, drivers = fruiting_score(
            WeatherFeatures(
                temperature_c=float(temperature),
                humidity_pct=float(humidity),
                precipitation_1h_mm=precipitation_rate,
            )
        )
        base_points.append(
            {
                "time": timestamp.isoformat().replace("+00:00", "Z"),
                "air_temperature_c": round(float(temperature), 2),
                "relative_humidity_pct": round(float(humidity), 1),
                "wind_speed_mps": None if wind is None else round(float(wind), 2),
                "precipitation_mm": round(precipitation_mm, 2),
                "precipitation_window_hours": precipitation_window_hours,
                "precipitation_rate_mm_h": round(precipitation_rate, 3),
                "fruiting_score_base": round(score, 4),
                "drivers": drivers,
            }
        )

    points = enrich_precipitation_memory(base_points)
    for point in points:
        base_score = float(point["fruiting_score_base"])
        moisture_memory = float(point["moisture_memory_index"])
        adjusted = clamp01(0.78 * base_score + 0.22 * moisture_memory)
        point["fruiting_score"] = round(adjusted, 4)
        if moisture_memory >= 0.55:
            point["drivers"] = [*point["drivers"], "antecedent rainfall memory"]

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for point in points:
        grouped[point["time"][:10]].append(point)

    daily: list[dict[str, Any]] = []
    for date, items in sorted(grouped.items()):
        scores = [float(item["fruiting_score"]) for item in items]
        temperatures = [float(item["air_temperature_c"]) for item in items]
        humidities = [float(item["relative_humidity_pct"]) for item in items]
        memories = [float(item["moisture_memory_index"]) for item in items]
        best = max(items, key=lambda item: float(item["fruiting_score"]))
        drivers: list[str] = []
        for item in sorted(items, key=lambda item: float(item["fruiting_score"]), reverse=True):
            for driver in item["drivers"]:
                if driver not in drivers:
                    drivers.append(driver)

        mean_score = sum(scores) / len(scores)
        peak_score = max(scores)
        ranking_score = 0.65 * peak_score + 0.35 * mean_score
        daily.append(
            {
                "date": date,
                "mean_fruiting_score": round(mean_score, 4),
                "peak_fruiting_score": round(peak_score, 4),
                "ranking_score": round(ranking_score, 4),
                "best_time": best["time"],
                "temperature_mean_c": round(sum(temperatures) / len(temperatures), 2),
                "humidity_mean_pct": round(sum(humidities) / len(humidities), 1),
                "precipitation_total_mm": round(
                    sum(float(item["precipitation_mm"]) for item in items),
                    2,
                ),
                "moisture_memory_mean": round(sum(memories) / len(memories), 4),
                "antecedent_precip_72h_peak_mm": round(
                    max(float(item["antecedent_precip_72h_mm"]) for item in items),
                    2,
                ),
                "sample_count": len(items),
                "drivers": drivers[:5],
            }
        )

    best_day = max(daily, key=lambda item: float(item["ranking_score"])) if daily else None
    return {
        "source": "MET Norway Locationforecast 2.0",
        "generated_from": points[0]["time"] if points else None,
        "horizon_days": len(daily),
        "points": points,
        "days": daily,
        "best_day": best_day,
        "model": "weather-memory fruiting heuristic v1.0",
        "memory_semantics": (
            "Decaying rainfall memory uses precipitation inside the available MET timeline. "
            "Warm-up coverage is reported and is not observed pre-forecast rainfall."
        ),
        "warning": (
            "Temporal score is explainable decision support. It is not a trained species "
            "phenology model, an occurrence probability, or observed historical rainfall."
        ),
    }
