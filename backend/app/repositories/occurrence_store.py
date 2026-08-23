from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


@dataclass(frozen=True)
class NormalizedOccurrence:
    source_record_id: str
    source_id: str
    scientific_name: str | None
    observed_at: str | None
    lat: float | None
    lon: float | None
    h3: str | None
    coordinate_uncertainty_m: float | None
    payload_hash: str
    raw_json: str


def _first(record: dict[str, Any], keys: tuple[str, ...]) -> Any:
    lowered = {str(key).casefold(): value for key, value in record.items()}
    for key in keys:
        if key.casefold() in lowered:
            return lowered[key.casefold()]
    return None


def _float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def extract_records(payload: dict | list | None) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("items", "records", "observations", "data", "results"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return [payload]


def normalize_occurrence(
    record: dict[str, Any],
    *,
    source_id: str = "artskart",
    h3_resolution: int = 9,
) -> NormalizedOccurrence:
    raw_json = json.dumps(record, ensure_ascii=False, sort_keys=True, default=str)
    payload_hash = hashlib.sha256(raw_json.encode("utf-8")).hexdigest()
    record_id = _first(
        record,
        ("id", "observationId", "occurrenceId", "recordId", "catalogNumber"),
    )
    scientific_name = _first(
        record,
        ("scientificName", "scientific_name", "taxonName", "species", "name"),
    )
    observed_at = _first(
        record,
        ("eventDate", "observationDate", "observedAt", "date", "datetime"),
    )
    lat = _float(_first(record, ("decimalLatitude", "latitude", "lat")))
    lon = _float(_first(record, ("decimalLongitude", "longitude", "lon", "lng")))
    uncertainty = _float(
        _first(
            record,
            ("coordinateUncertaintyInMeters", "coordinateUncertainty", "accuracy", "precision"),
        )
    )

    h3_cell = None
    if lat is not None and lon is not None and -90 <= lat <= 90 and -180 <= lon <= 180:
        import h3

        h3_cell = h3.latlng_to_cell(lat, lon, h3_resolution)

    identifier = str(record_id).strip() if record_id is not None else payload_hash
    return NormalizedOccurrence(
        source_record_id=f"{source_id}:{identifier}",
        source_id=source_id,
        scientific_name=None if scientific_name is None else str(scientific_name).strip() or None,
        observed_at=None if observed_at is None else str(observed_at).strip() or None,
        lat=lat,
        lon=lon,
        h3=h3_cell,
        coordinate_uncertainty_m=uncertainty,
        payload_hash=payload_hash,
        raw_json=raw_json,
    )


class OccurrenceStoreRepository:
    """Portable presence-only occurrence warehouse for SQLite or PostgreSQL."""

    def __init__(self, database_url: str, engine: Engine | None = None) -> None:
        self.engine = engine or create_engine(database_url, pool_pre_ping=True)

    def initialize(self) -> None:
        statements = (
            """
            CREATE TABLE IF NOT EXISTS occurrence_records (
              source_record_id TEXT PRIMARY KEY,
              source_id TEXT NOT NULL,
              scientific_name TEXT,
              observed_at TEXT,
              lat REAL,
              lon REAL,
              h3 TEXT,
              coordinate_uncertainty_m REAL,
              payload_hash TEXT NOT NULL,
              raw_json TEXT NOT NULL,
              ingested_at TEXT NOT NULL
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_occurrence_h3 ON occurrence_records(h3)",
            """
            CREATE INDEX IF NOT EXISTS idx_occurrence_name
            ON occurrence_records(scientific_name)
            """,
        )
        with self.engine.begin() as conn:
            for statement in statements:
                conn.execute(text(statement))

    def upsert_many(self, records: list[NormalizedOccurrence]) -> int:
        if not records:
            return 0
        self.initialize()
        statement = text(
            """
            INSERT INTO occurrence_records (
              source_record_id, source_id, scientific_name, observed_at,
              lat, lon, h3, coordinate_uncertainty_m, payload_hash,
              raw_json, ingested_at
            ) VALUES (
              :source_record_id, :source_id, :scientific_name, :observed_at,
              :lat, :lon, :h3, :coordinate_uncertainty_m, :payload_hash,
              :raw_json, :ingested_at
            )
            ON CONFLICT(source_record_id) DO UPDATE SET
              scientific_name = excluded.scientific_name,
              observed_at = excluded.observed_at,
              lat = excluded.lat,
              lon = excluded.lon,
              h3 = excluded.h3,
              coordinate_uncertainty_m = excluded.coordinate_uncertainty_m,
              payload_hash = excluded.payload_hash,
              raw_json = excluded.raw_json,
              ingested_at = excluded.ingested_at
            """
        )
        now = datetime.now(UTC).isoformat()
        rows = [
            {
                **record.__dict__,
                "ingested_at": now,
            }
            for record in records
        ]
        with self.engine.begin() as conn:
            conn.execute(statement, rows)
        return len(rows)

    def count(self, scientific_name: str | None = None) -> int:
        self.initialize()
        with self.engine.connect() as conn:
            if scientific_name:
                value = conn.execute(
                    text(
                        "SELECT COUNT(*) FROM occurrence_records "
                        "WHERE lower(scientific_name) = lower(:name)"
                    ),
                    {"name": scientific_name},
                ).scalar_one()
            else:
                value = conn.execute(text("SELECT COUNT(*) FROM occurrence_records")).scalar_one()
        return int(value)
