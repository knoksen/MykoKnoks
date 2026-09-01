from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any, Protocol

from app.clients.frost import FrostClient, FrostNotConfigured


class FrostLikeClient(Protocol):
    DAILY_PRECIPITATION_ELEMENT: str

    async def nearest_precipitation_sources(
        self,
        lat: float,
        lon: float,
        *,
        max_count: int = 3,
    ) -> list[dict[str, Any]]: ...

    async def daily_precipitation(
        self,
        sources: list[str],
        *,
        start: date,
        end: date,
        qualities: str = "0,1,2,3,4",
    ) -> list[dict[str, Any]]: ...


def _source_id(item: dict[str, Any]) -> str | None:
    value = item.get("id") or item.get("sourceId")
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _distance_km(item: dict[str, Any]) -> float | None:
    value = item.get("distance")
    try:
        return None if value is None else round(float(value), 3)
    except (TypeError, ValueError):
        return None


def _daily_values(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        reference_time = row.get("referenceTime")
        source_id = row.get("sourceId")
        observations = row.get("observations", [])
        if not reference_time or not source_id or not isinstance(observations, list):
            continue
        for observation in observations:
            if not isinstance(observation, dict):
                continue
            if observation.get("elementId") != FrostClient.DAILY_PRECIPITATION_ELEMENT:
                continue
            try:
                value = max(0.0, float(observation.get("value")))
            except (TypeError, ValueError):
                continue
            key = (str(source_id), str(reference_time))
            if key in seen:
                continue
            seen.add(key)
            values.append(
                {
                    "source_id": str(source_id),
                    "reference_time": str(reference_time),
                    "value_mm": round(value, 3),
                    "quality_code": observation.get("qualityCode"),
                    "time_offset": observation.get("timeOffset"),
                    "time_resolution": observation.get("timeResolution"),
                }
            )
    return sorted(values, key=lambda item: item["reference_time"])


def _sum_latest(values: list[dict[str, Any]], count: int) -> float | None:
    if len(values) < count:
        return None
    return round(sum(float(item["value_mm"]) for item in values[-count:]), 3)


class ObservedPrecipitationService:
    """Historical Frost precipitation with explicit standard-period semantics."""

    def __init__(self, client: FrostLikeClient, *, nearest_station_count: int = 3) -> None:
        self.client = client
        self.nearest_station_count = max(1, min(10, nearest_station_count))

    async def history(
        self,
        lat: float,
        lon: float,
        *,
        days: int = 14,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = (now or datetime.now(UTC)).astimezone(UTC)
        horizon = max(7, min(31, days))
        end = current.date()
        start = end - timedelta(days=horizon + 2)

        try:
            sources = await self.client.nearest_precipitation_sources(
                lat,
                lon,
                max_count=self.nearest_station_count,
            )
        except FrostNotConfigured:
            return {
                "available": False,
                "provider": "MET Norway Frost",
                "reason": "FROST_CLIENT_ID not configured",
                "observed": False,
                "probability_claim_allowed": False,
            }

        source_meta = [
            {
                "id": source_id,
                "name": item.get("name"),
                "distance_km": _distance_km(item),
            }
            for item in sources
            if (source_id := _source_id(item)) is not None
        ]
        if not source_meta:
            return {
                "available": False,
                "provider": "MET Norway Frost",
                "reason": "No current precipitation source found near requested coordinate",
                "observed": True,
                "probability_claim_allowed": False,
            }

        selected_source: dict[str, Any] | None = None
        daily: list[dict[str, Any]] = []
        for source in source_meta:
            rows = await self.client.daily_precipitation(
                [source["id"]],
                start=start,
                end=end,
            )
            candidate = _daily_values(rows)
            if candidate:
                selected_source = source
                daily = candidate[-horizon:]
                break

        if selected_source is None:
            return {
                "available": False,
                "provider": "MET Norway Frost",
                "reason": "Nearest candidate stations returned no usable daily precipitation",
                "observed": True,
                "candidate_sources": source_meta,
                "probability_claim_allowed": False,
            }

        latest_reference = daily[-1]["reference_time"] if daily else None
        return {
            "available": True,
            "provider": "MET Norway Frost",
            "observed": True,
            "center": [lon, lat],
            "source": selected_source,
            "candidate_sources": source_meta,
            "element": FrostClient.DAILY_PRECIPITATION_ELEMENT,
            "daily_standard_periods": daily,
            "antecedent_precip_24h_standard_mm": _sum_latest(daily, 1),
            "antecedent_precip_72h_standard_mm": _sum_latest(daily, 3),
            "antecedent_precip_168h_standard_mm": _sum_latest(daily, 7),
            "latest_reference_time": latest_reference,
            "data_quality": {
                "daily_periods_available": len(daily),
                "requested_history_days": horizon,
                "source_distance_km": selected_source.get("distance_km"),
                "meaning": (
                    "Coverage and station distance describe observational support; they are not "
                    "statistical model confidence."
                ),
            },
            "aggregation_semantics": (
                "Totals use Frost's standard P1D precipitation series with default level/time offset. "
                "24h/72h/168h labels here mean the latest 1/3/7 standard daily periods, not rolling "
                "windows ending at the request timestamp."
            ),
            "scientific_guardrail": (
                "These are historical station observations from the selected Frost source. Station "
                "measurements are not direct per-H3 soil moisture and are kept separate from MET "
                "Locationforecast precipitation memory."
            ),
            "probability_claim_allowed": False,
        }
