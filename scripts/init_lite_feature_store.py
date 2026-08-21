"""Initialize the lightweight SQLite H3 feature store used on Ultra.cc."""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS env_features (
    h3 TEXT PRIMARY KEY,
    h3_resolution INTEGER NOT NULL DEFAULT 9,
    geometry_json TEXT,
    elevation_m REAL,
    terrain TEXT,
    grassland_proxy REAL,
    forest_edge_proxy REAL,
    soil_moisture_proxy REAL,
    completeness REAL NOT NULL DEFAULT 0.0,
    feature_version TEXT NOT NULL DEFAULT 'norway-live-v0.2',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_env_features_resolution
    ON env_features(h3_resolution);

CREATE TABLE IF NOT EXISTS env_feature_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    h3 TEXT NOT NULL,
    source_id TEXT NOT NULL,
    source_layer TEXT,
    payload TEXT NOT NULL,
    quality TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_env_evidence_h3
    ON env_feature_evidence(h3);
"""


def initialize(path: Path) -> None:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA)
        conn.commit()
    print(f"initialized SQLite H3 feature store: {path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    args = parser.parse_args()
    initialize(args.database)


if __name__ == "__main__":
    main()
