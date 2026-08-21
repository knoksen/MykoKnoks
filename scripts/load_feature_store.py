"""Load JSONL produced by ingest_live_features.py into PostGIS."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import psycopg


UPSERT_FEATURE = """
INSERT INTO env_features (
  h3, h3_resolution, geom, elevation_m, terrain,
  grassland_proxy, forest_edge_proxy, soil_moisture_proxy,
  completeness, feature_version, updated_at
) VALUES (
  %(h3)s,
  %(resolution)s,
  ST_SetSRID(ST_GeomFromGeoJSON(%(geometry)s), 4326),
  %(elevation_m)s,
  %(terrain)s,
  %(grassland_proxy)s,
  %(forest_edge_proxy)s,
  %(soil_moisture_proxy)s,
  %(completeness)s,
  %(feature_version)s,
  now()
)
ON CONFLICT (h3) DO UPDATE SET
  h3_resolution = EXCLUDED.h3_resolution,
  geom = EXCLUDED.geom,
  elevation_m = EXCLUDED.elevation_m,
  terrain = EXCLUDED.terrain,
  grassland_proxy = EXCLUDED.grassland_proxy,
  forest_edge_proxy = EXCLUDED.forest_edge_proxy,
  soil_moisture_proxy = EXCLUDED.soil_moisture_proxy,
  completeness = EXCLUDED.completeness,
  feature_version = EXCLUDED.feature_version,
  updated_at = now()
"""

INSERT_EVIDENCE = """
INSERT INTO env_feature_evidence (h3, source_id, source_layer, payload, quality)
VALUES (%(h3)s, %(source_id)s, %(source_layer)s, %(payload)s::jsonb, %(quality)s::jsonb)
"""


def evidence_rows(row: dict) -> list[dict]:
    snap = row["snapshot"]
    mapping = {
        "nibio_ar5": snap.get("ar5_evidence"),
        "nibio_sr16": snap.get("sr16_evidence"),
        "ngu_losmasse": snap.get("loose_sediment_evidence"),
    }
    return [
        {
            "h3": row["h3"],
            "source_id": source_id,
            "source_layer": None,
            "payload": json.dumps(payload, ensure_ascii=False),
            "quality": json.dumps({"completeness": snap.get("completeness", 0.0)}),
        }
        for source_id, payload in mapping.items()
        if payload is not None
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL", "postgresql://mykoknoks:mykoknoks@localhost:5432/mykoknoks"),
    )
    args = parser.parse_args()

    written = 0
    database_url = args.database_url.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(database_url) as conn, args.jsonl.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            snap = row["snapshot"]
            params = {
                "h3": row["h3"],
                "resolution": int(row.get("resolution", 9)),
                "geometry": json.dumps(row["geometry"]),
                "elevation_m": snap.get("elevation_m"),
                "terrain": snap.get("terrain"),
                "grassland_proxy": snap.get("grassland_proxy", 0.5),
                "forest_edge_proxy": snap.get("forest_edge_proxy", 0.5),
                "soil_moisture_proxy": snap.get("soil_moisture_proxy", 0.5),
                "completeness": snap.get("completeness", 0.0),
                "feature_version": row.get("feature_version", "norway-live-v0.2"),
            }
            conn.execute(UPSERT_FEATURE, params)
            for evidence in evidence_rows(row):
                conn.execute(INSERT_EVIDENCE, evidence)
            written += 1
        conn.commit()
    print(f"loaded {written} H3 feature rows")


if __name__ == "__main__":
    main()
