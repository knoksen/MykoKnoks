from __future__ import annotations

import json
from typing import Any


HABITAT_FEATURE_COLUMNS = (
    "open_land_score",
    "wetland_score",
    "forest_score",
    "substrate_moisture_score",
    "elevation_m",
    "slope_deg",
    "terrain_roughness_m",
)


def spatial_block(cell: str, block_resolution: int = 6) -> str:
    import h3

    resolution = h3.get_resolution(cell)
    if block_resolution < 0 or block_resolution > resolution:
        raise ValueError(
            f"block_resolution must be between 0 and cell resolution {resolution}"
        )
    return h3.cell_to_parent(cell, block_resolution)


def feature_vector_from_store_row(row: dict[str, Any]) -> dict[str, float] | None:
    raw = row.get("gis_features_json")
    if isinstance(raw, str):
        try:
            gis = json.loads(raw)
        except json.JSONDecodeError:
            return None
    elif isinstance(raw, dict):
        gis = raw
    else:
        return None
    if not isinstance(gis, dict):
        return None

    values: dict[str, Any] = {
        "open_land_score": gis.get("open_land_score"),
        "wetland_score": gis.get("wetland_score"),
        "forest_score": gis.get("forest_score"),
        "substrate_moisture_score": gis.get("substrate_moisture_score"),
        "elevation_m": row.get("elevation_m"),
        "slope_deg": gis.get("slope_deg"),
        "terrain_roughness_m": gis.get("terrain_roughness_m"),
    }
    if any(value is None for value in values.values()):
        return None
    try:
        return {key: float(value) for key, value in values.items()}
    except (TypeError, ValueError):
        return None


def build_training_rows(
    feature_rows: list[dict[str, Any]],
    presence_cells: list[str],
    background_cells: list[str],
    *,
    block_resolution: int = 6,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Join H3 environmental vectors to presence and operator-supplied background cells.

    Presence always wins when the same H3 cell is supplied as background. Background
    rows are labelled `present=0` for classifier mechanics but remain explicitly marked
    `sample_role=background`; they are not asserted biological absences.
    """
    features = {str(row["h3"]): row for row in feature_rows if row.get("h3")}
    presences = set(map(str, presence_cells))
    backgrounds = set(map(str, background_cells)) - presences

    output: list[dict[str, Any]] = []
    missing_features = 0
    incomplete_vectors = 0

    for sample_role, cells, target in (
        ("presence", sorted(presences), 1),
        ("background", sorted(backgrounds), 0),
    ):
        for cell in cells:
            stored = features.get(cell)
            if stored is None:
                missing_features += 1
                continue
            vector = feature_vector_from_store_row(stored)
            if vector is None:
                incomplete_vectors += 1
                continue
            output.append(
                {
                    "h3": cell,
                    "spatial_block": spatial_block(cell, block_resolution),
                    "sample_role": sample_role,
                    "present": target,
                    **vector,
                }
            )

    stats = {
        "presence_requested": len(presences),
        "background_requested": len(backgrounds),
        "rows_written": len(output),
        "presence_rows": sum(row["present"] == 1 for row in output),
        "background_rows": sum(row["present"] == 0 for row in output),
        "missing_feature_rows": missing_features,
        "incomplete_feature_vectors": incomplete_vectors,
    }
    return output, stats
