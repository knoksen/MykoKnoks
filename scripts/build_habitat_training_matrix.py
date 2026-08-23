"""Build a habitat SDM training CSV from MykoKnoks SQLite stores.

Presence cells come from the Artskart occurrence warehouse. Background cells must be
supplied explicitly by the operator; this script never invents absence labels.
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.training_matrix import (  # noqa: E402
    HABITAT_FEATURE_COLUMNS,
    build_training_rows,
)


def read_background_cells(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8-sig")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return []

    if path.suffix.casefold() == ".csv":
        reader = csv.DictReader(lines)
        if reader.fieldnames and "h3" in reader.fieldnames:
            return [str(row["h3"]).strip() for row in reader if row.get("h3")]
    return [line.split(",", 1)[0].strip() for line in lines if line.split(",", 1)[0].strip() != "h3"]


def load_presence_cells(
    conn: sqlite3.Connection,
    species: str,
    max_uncertainty_m: float | None,
) -> list[str]:
    sql = (
        "SELECT DISTINCT h3 FROM occurrence_records "
        "WHERE h3 IS NOT NULL AND lower(scientific_name) = lower(?)"
    )
    params: list[object] = [species]
    if max_uncertainty_m is not None:
        sql += " AND (coordinate_uncertainty_m IS NULL OR coordinate_uncertainty_m <= ?)"
        params.append(max_uncertainty_m)
    return [str(row[0]) for row in conn.execute(sql, params).fetchall()]


def load_feature_rows(conn: sqlite3.Connection, cells: list[str]) -> list[dict]:
    if not cells:
        return []
    rows: list[dict] = []
    batch_size = 700
    for start in range(0, len(cells), batch_size):
        batch = cells[start : start + batch_size]
        placeholders = ",".join("?" for _ in batch)
        cursor = conn.execute(
            f"""
            SELECT h3, elevation_m, gis_features_json
            FROM env_features
            WHERE h3 IN ({placeholders})
            """,
            batch,
        )
        columns = [item[0] for item in cursor.description]
        rows.extend(dict(zip(columns, row)) for row in cursor.fetchall())
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--species", required=True)
    parser.add_argument("--background", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--block-resolution", type=int, default=6)
    parser.add_argument("--max-uncertainty-m", type=float, default=1000.0)
    args = parser.parse_args()

    database = args.database.expanduser().resolve()
    if not database.exists():
        raise SystemExit(f"Database not found: {database}")

    backgrounds = read_background_cells(args.background)
    with sqlite3.connect(database) as conn:
        presence_table = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='occurrence_records'"
        ).fetchone()[0]
        if not presence_table:
            raise SystemExit("occurrence_records table is missing; ingest Artskart records first")

        presences = load_presence_cells(conn, args.species, args.max_uncertainty_m)
        requested = sorted(set(presences) | set(backgrounds))
        feature_rows = load_feature_rows(conn, requested)

    rows, stats = build_training_rows(
        feature_rows,
        presences,
        backgrounds,
        block_resolution=args.block_resolution,
    )
    if not rows:
        raise SystemExit(
            "No complete training rows were produced. Full v1 H3 ingestion with GIS and terrain "
            "metrics is required for the requested cells."
        )
    if not any(row["present"] == 1 for row in rows):
        raise SystemExit("No presence rows with complete environmental vectors were available.")
    if not any(row["present"] == 0 for row in rows):
        raise SystemExit("No background rows with complete environmental vectors were available.")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "h3",
        "spatial_block",
        "sample_role",
        "present",
        *HABITAT_FEATURE_COLUMNS,
    ]
    with args.out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(json.dumps(stats, indent=2))
    print(f"wrote={args.out.resolve()}")
    print(
        "Scientific boundary: present=0 rows are operator-supplied background, not confirmed absence."
    )


if __name__ == "__main__":
    main()
