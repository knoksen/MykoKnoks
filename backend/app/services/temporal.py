from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from app.scoring import WeatherFeatures, fruiting_score


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _precipitation(data: dict[str, Any]) -> tuple[float, int]:
    for key, hours in (("next_1_hours", 1), ("next_6_hours", 6), ("next_12_hours", 12)):
        details = data.get(key, {}).get("details", {})
        amount = details.get("precipitation_amount")
        if amount is not None:
            return max(0.0, float(amount)), hours
    return 0.0, 1


def build_temporal_forecast(payload: dict[str, Any], days: int = 10) -> dict[str, Any]:
    """Convert MET Locationforecast timeseries to an auditable fruiting timeline.

    This deliberately remains an explainable weather-driven heuristic. It is not a
    trained phenology model and does not represent species occurrence probability.
    """

    raw_series = payload.get("properties", {}).get("timeseries", [])
    if not raw_series:
        return {
            "source": "MET Norway Locationforecast 2.0",
            "points": [],
            "days": [],
            "best_day": None,
            "model": "weather-driven fruiting heuristic",
            "warning": "No MET forecast timeseries returned.",
        }

    first_time = _parse_time(raw_series[0]["time"])
    cutoff = first_time + timedelta(days=max(1, min(days, 14)))
    points: list[dict[str, Any]] = []

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

        points.append(
            {
                "time": timestamp.isoformat().replace("+00:00", "Z"),
                "air_temperature_c": round(float(temperature), 2),
                "relative_humidity_pct": round(float(humidity), 1),
                "wind_speed_mps": None if wind is None else round(float(wind), 2),
                "precipitation_mm": round(precipitation_mm, 2),
                "precipitation_window_hours": precipitation_window_hours,
                "precipitation_rate_mm_h": round(precipitation_rate, 3),
                "fruiting_score": round(score, 4),
                "drivers": drivers,
            }
        )

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for point in points:
        grouped[point["time"][:10]].append(point)

    daily: list[dict[str, Any]] = []
    for date, items in sorted(grouped.items()):
        scores = [float(item["fruiting_score"]) for item in items]
        temperatures = [float(item["air_temperature_c"]) for item in items]
        humidities = [float(item["relative_humidity_pct"]) for item in items]
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
                "precipitation_total_mm": round(sum(float(item["precipitation_mm"]) for item in items), 2),
                "sample_count": len(items),
                "drivers": drivers[:4],
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
        "model": "weather-driven fruiting heuristic",
        "warning": (
            "Temporal fruiting score is explainable decision support from forecast weather. "
            "It is not a trained species phenology model or occurrence probability."
        ),
    }
