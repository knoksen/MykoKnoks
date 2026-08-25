import json

import h3

from app.services.training_matrix import build_training_rows, feature_vector_from_store_row


def _stored(cell: str, elevation: float = 50.0) -> dict:
    return {
        "h3": cell,
        "elevation_m": elevation,
        "gis_features_json": json.dumps(
            {
                "open_land_score": 0.9,
                "wetland_score": 0.2,
                "forest_score": 0.1,
                "substrate_moisture_score": 0.7,
                "slope_deg": 3.0,
                "terrain_roughness_m": 1.2,
            }
        ),
    }


def test_training_matrix_presence_overrides_background() -> None:
    presence = h3.latlng_to_cell(58.735, 5.647, 9)
    background = h3.latlng_to_cell(58.745, 5.657, 9)
    rows, stats = build_training_rows(
        [_stored(presence), _stored(background)],
        [presence],
        [presence, background],
        block_resolution=6,
    )

    assert len(rows) == 2
    assert stats["presence_rows"] == 1
    assert stats["background_rows"] == 1
    by_cell = {row["h3"]: row for row in rows}
    assert by_cell[presence]["present"] == 1
    assert by_cell[presence]["sample_role"] == "presence"
    assert by_cell[background]["sample_role"] == "background"
    assert h3.get_resolution(by_cell[presence]["spatial_block"]) == 6


def test_incomplete_vector_is_rejected() -> None:
    cell = h3.latlng_to_cell(58.735, 5.647, 9)
    row = _stored(cell)
    payload = json.loads(row["gis_features_json"])
    payload["slope_deg"] = None
    row["gis_features_json"] = json.dumps(payload)

    assert feature_vector_from_store_row(row) is None
