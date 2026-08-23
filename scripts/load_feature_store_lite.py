"""Load MykoKnoks H3 JSONL snapshots into the lightweight SQLite store."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from init_lite_feature_store import initialize


UPSERT_FEATURE = """
INSERT INTO env_features (
    h3, h3_resolution, geometry_json, elevation_m, terrain,
    grassland_proxy, forest_edge_proxy, soil_moisture_proxy,
    gis_features_json, completeness, feature_version, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
ON CONFLICT(h3) DO UPDATE SET
    h3_resolution = excluded.h3_resolution,
    geometry_json = excluded.geometry_json,
    elevation_m = excluded.elevation_m,
    terrain = excluded.terrain,
    grassland_proxy = excluded.grassland_proxy,
    forest_edge_proxy = excluded.forest_edge_proxy,
    soil_moisture_proxy = excluded.soil_moisture_proxy,
    gis_features_json = excluded.gis_features_json,
    completeness = excluded.completeness,
    feature_version = excluded.feature_version,
    updated_at = CURRENT_TIMESTAMP
"""

INSERT_EVIDENCE = """
INSERT INTO env_feature_evidence (h3, source_id, source_layer, payload, quality)
VALUES (?, ?, ?, ?, ?)
"""


def evidence_rows(row: dict) -> list[tuple[str, str, str | None, str, str]]:
    snap = row["snapshot"]
    mapping = {
        "nibio_ar5": snap.get("ar5_evidence"),
        "nibio_sr16": snap.get("sr16_evidence"),
        "ngu_losmasse": snap.get("loose_sediment_evidence"),
    }
    return [
        (
            row["h3"],
            source_id,
            None,
            json.dumps(payload, ensure_ascii=False),
            json.dumps({"completeness": snap.get("completeness", 0.0)}),
        )
        for source_id, payload in mapping.items()
        if payload is not None
    ]


def load(jsonl: Path, database: Path) -> int:
    initialize(database)
    database = database.expanduser().resolve()
    written = 0

    with sqlite3.connect(database) as conn, jsonl.open(encoding="utf-8") as handle:
        conn.execute("PRAGMA journal_mode=WAL")
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            snap = row["snapshot"]
            conn.execute(
                UPSERT_FEATURE,
                (
                    row["h3"],
                    int(row.get("resolution", 9)),
                    json.dumps(row.get("geometry"), ensure_ascii=False),
                    snap.get("elevation_m"),
                    snap.get("terrain"),
                    snap.get("grassland_proxy", 0.5),
                    snap.get("forest_edge_proxy", 0.5),
                    snap.get("soil_moisture_proxy", 0.5),
                    json.dumps(snap.get("normalized_gis") or {}, ensure_ascii=False),
                    snap.get("completeness", 0.0),
                    row.get("feature_version", "prediction-gis-v0.9"),
                ),
            )
            evidence = evidence_rows(row)
            if evidence:
                conn.executemany(INSERT_EVIDENCE, evidence)
            written += 1
        conn.commit()

    return written


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--database", type=Path, required=True)
    args = parser.parse_args()
    written = load(args.jsonl, args.database)
    print(f"loaded {written} H3 feature rows into {args.database.expanduser().resolve()}")


if __name__ == "__main__":
    main()
