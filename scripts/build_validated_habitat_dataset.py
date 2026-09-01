"""Build a reproducible presence-background habitat dataset from the local stores."""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.repositories.occurrence_store import NormalizedOccurrence  # noqa: E402
from app.services.background_sampling import sample_background_cells  # noqa: E402
from app.services.dataset_manifest import build_dataset_manifest  # noqa: E402
from app.services.occurrence_quality import filter_occurrences  # noqa: E402
from app.services.training_matrix import (  # noqa: E402
    HABITAT_FEATURE_COLUMNS,
    build_training_rows,
    feature_vector_from_store_row,
)


def load_occurrences(conn: sqlite3.Connection, species: str) -> list[NormalizedOccurrence]:
    cursor = conn.execute(
        """
        SELECT source_record_id, source_id, scientific_name, observed_at,
               lat, lon, h3, coordinate_uncertainty_m, payload_hash, raw_json
        FROM occurrence_records
        WHERE lower(scientific_name) = lower(?)
        ORDER BY source_record_id
        """,
        (species,),
    )
    return [NormalizedOccurrence(*row) for row in cursor.fetchall()]


def load_complete_feature_rows(conn: sqlite3.Connection) -> dict[str, dict]:
    cursor = conn.execute(
        """
        SELECT h3, elevation_m, gis_features_json
        FROM env_features
        WHERE h3 IS NOT NULL AND gis_features_json IS NOT NULL
        ORDER BY h3
        """
    )
    columns = [item[0] for item in cursor.description]
    complete: dict[str, dict] = {}
    for raw in cursor:
        row = dict(zip(columns, raw))
        if feature_vector_from_store_row(row) is not None:
            complete[str(row["h3"])] = row
    return complete


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--species", required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--background-size", type=int)
    parser.add_argument("--background-ratio", type=float, default=3.0)
    parser.add_argument("--seed", type=int, default=20260901)
    parser.add_argument("--buffer-rings", type=int, default=1)
    parser.add_argument("--stratum-resolution", type=int, default=6)
    parser.add_argument("--block-resolution", type=int, default=6)
    parser.add_argument("--max-uncertainty-m", type=float, default=1000.0)
    args = parser.parse_args()

    database = args.database.expanduser().resolve()
    if not database.exists():
        raise SystemExit(f"Database not found: {database}")
    if args.background_ratio <= 0:
        raise SystemExit("--background-ratio must be > 0")

    with sqlite3.connect(database) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        required = {"occurrence_records", "env_features"}
        if not required.issubset(tables):
            missing = ", ".join(sorted(required - tables))
            raise SystemExit(f"Missing required table(s): {missing}")

        raw_occurrences = load_occurrences(conn, args.species)
        feature_rows = load_complete_feature_rows(conn)

    quality = filter_occurrences(
        raw_occurrences,
        species=args.species,
        max_coordinate_uncertainty_m=args.max_uncertainty_m,
    )
    presence_cells = sorted({record.h3 for record in quality.records if record.h3})
    if not presence_cells:
        raise SystemExit("No quality-filtered presence cells are available for this species.")

    presence_with_features = sorted(set(presence_cells) & set(feature_rows))
    missing_presence_features = len(presence_cells) - len(presence_with_features)
    if not presence_with_features:
        raise SystemExit(
            "No presence cells have complete habitat vectors. Run full GIS/terrain ingestion first."
        )

    requested_background = args.background_size
    if requested_background is None:
        requested_background = max(1, round(len(presence_with_features) * args.background_ratio))

    background = sample_background_cells(
        list(feature_rows),
        presence_with_features,
        sample_size=requested_background,
        seed=args.seed,
        buffer_rings=args.buffer_rings,
        stratum_resolution=args.stratum_resolution,
    )
    if not background.cells:
        raise SystemExit("No eligible background cells remain after presence-buffer exclusion.")

    requested_cells = sorted(set(presence_with_features) | set(background.cells))
    training_rows, matrix_stats = build_training_rows(
        [feature_rows[cell] for cell in requested_cells],
        presence_with_features,
        background.cells,
        block_resolution=args.block_resolution,
    )

    if not training_rows:
        raise SystemExit("No training rows were produced.")

    h3_resolution = __import__("h3").get_resolution(requested_cells[0])
    manifest = build_dataset_manifest(
        species=args.species,
        h3_resolution=h3_resolution,
        spatial_block_resolution=args.block_resolution,
        feature_columns=list(HABITAT_FEATURE_COLUMNS),
        presence_cells=presence_with_features,
        background_cells=background.cells,
        max_coordinate_uncertainty_m=args.max_uncertainty_m,
        background_seed=args.seed,
        background_buffer_rings=args.buffer_rings,
        source_metadata={
            "occurrences": "Artskart presence-only warehouse",
            "environment": "MykoKnoks env_features AR5/SR16/NGU/terrain",
            "background_sampling": "H3 presence-buffer exclusion + spatial parent strata",
        },
    )
    manifest["quality"] = {
        "raw_occurrence_records": len(raw_occurrences),
        "accepted_occurrence_records": len(quality.records),
        "rejected_wrong_taxon": quality.rejected_wrong_taxon,
        "rejected_invalid_coordinate": quality.rejected_invalid_coordinate,
        "rejected_uncertainty": quality.rejected_uncertainty,
        "rejected_duplicate_event": quality.rejected_duplicate_event,
        "presence_cells_missing_complete_features": missing_presence_features,
        "complete_environment_cells": len(feature_rows),
    }
    manifest["background_sampling_stats"] = {
        "requested": requested_background,
        "selected": len(background.cells),
        "candidate_count": background.candidate_count,
        "excluded_presence_count": background.excluded_presence_count,
        "excluded_buffer_count": background.excluded_buffer_count,
        "strata_count": background.strata_count,
        "seed": background.seed,
    }
    manifest["matrix_stats"] = matrix_stats

    out_dir = args.out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "habitat-training.csv"
    manifest_path = out_dir / "dataset-manifest.json"

    fieldnames = [
        "h3",
        "spatial_block",
        "sample_role",
        "present",
        *HABITAT_FEATURE_COLUMNS,
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(training_rows)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(manifest["counts"], indent=2))
    print(json.dumps(manifest["quality"], indent=2))
    print(f"dataset_id={manifest['dataset_id']}")
    print(f"training_csv={csv_path}")
    print(f"manifest={manifest_path}")
    print(
        "Scientific boundary: background rows are sampling controls, not biological absence; "
        "calibrated remains false."
    )


if __name__ == "__main__":
    main()
