from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any


def canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def dataset_sha256(core: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(core).encode("utf-8")).hexdigest()


def build_dataset_manifest(
    *,
    species: str,
    h3_resolution: int,
    spatial_block_resolution: int,
    feature_columns: list[str],
    presence_cells: list[str],
    background_cells: list[str],
    max_coordinate_uncertainty_m: float | None,
    background_seed: int,
    background_buffer_rings: int,
    source_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic dataset identity plus non-identity generation metadata."""
    core = {
        "schema_version": 1,
        "species": species.strip(),
        "h3_resolution": int(h3_resolution),
        "spatial_block_resolution": int(spatial_block_resolution),
        "feature_columns": list(feature_columns),
        "presence_cells": sorted(set(map(str, presence_cells))),
        "background_cells": sorted(set(map(str, background_cells))),
        "max_coordinate_uncertainty_m": max_coordinate_uncertainty_m,
        "background_sampling": {
            "seed": int(background_seed),
            "buffer_rings": int(background_buffer_rings),
            "semantics": "presence-only background; not confirmed biological absence",
        },
        "sources": source_metadata or {},
    }
    digest = dataset_sha256(core)
    return {
        "dataset_id": f"sha256:{digest}",
        "dataset_sha256": digest,
        "generated_at": datetime.now(UTC).isoformat(),
        "calibrated": False,
        "scientific_boundary": (
            "Presence records are presence-only. Background cells are sampling controls, "
            "not confirmed absence. This manifest does not imply a calibrated probability model."
        ),
        "core": core,
        "counts": {
            "presence_cells": len(core["presence_cells"]),
            "background_cells": len(core["background_cells"]),
            "rows_expected": len(core["presence_cells"]) + len(core["background_cells"]),
        },
    }
