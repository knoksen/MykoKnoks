from __future__ import annotations

import h3

from app.repositories.occurrence_store import NormalizedOccurrence
from app.services.background_sampling import sample_background_cells
from app.services.dataset_manifest import build_dataset_manifest
from app.services.occurrence_quality import filter_occurrences
from app.services.training_matrix import HABITAT_FEATURE_COLUMNS


def _record(
    record_id: str,
    *,
    species: str = "Psilocybe semilanceata",
    lat: float = 58.735,
    lon: float = 5.647,
    observed_at: str = "2026-09-01",
    uncertainty: float | None = 50.0,
) -> NormalizedOccurrence:
    return NormalizedOccurrence(
        source_record_id=f"artskart:{record_id}",
        source_id="artskart",
        scientific_name=species,
        observed_at=observed_at,
        lat=lat,
        lon=lon,
        h3=h3.latlng_to_cell(lat, lon, 9),
        coordinate_uncertainty_m=uncertainty,
        payload_hash=record_id * 8,
        raw_json="{}",
    )


def test_background_sampling_is_deterministic_and_excludes_presence_buffer() -> None:
    presence = h3.latlng_to_cell(58.735, 5.647, 9)
    candidates = sorted(h3.grid_disk(presence, 5))

    first = sample_background_cells(
        candidates,
        [presence],
        sample_size=12,
        seed=42,
        buffer_rings=1,
        stratum_resolution=8,
    )
    second = sample_background_cells(
        list(reversed(candidates)),
        [presence],
        sample_size=12,
        seed=42,
        buffer_rings=1,
        stratum_resolution=8,
    )

    forbidden = set(h3.grid_disk(presence, 1))
    assert first.cells == second.cells
    assert len(first.cells) == 12
    assert not (set(first.cells) & forbidden)
    assert first.excluded_presence_count == 1
    assert first.excluded_buffer_count > 0


def test_occurrence_quality_filters_uncertainty_taxon_and_duplicate_events() -> None:
    records = [
        _record("a"),
        _record("b"),
        _record("c", uncertainty=2500.0),
        _record("d", species="Amanita muscaria"),
    ]

    result = filter_occurrences(
        records,
        species="Psilocybe semilanceata",
        max_coordinate_uncertainty_m=1000.0,
    )

    assert [record.source_record_id for record in result.records] == ["artskart:a"]
    assert result.rejected_duplicate_event == 1
    assert result.rejected_uncertainty == 1
    assert result.rejected_wrong_taxon == 1


def test_dataset_identity_is_stable_for_equivalent_inputs() -> None:
    kwargs = {
        "species": "Psilocybe semilanceata",
        "h3_resolution": 9,
        "spatial_block_resolution": 6,
        "feature_columns": list(HABITAT_FEATURE_COLUMNS),
        "max_coordinate_uncertainty_m": 1000.0,
        "background_seed": 42,
        "background_buffer_rings": 1,
        "source_metadata": {"occurrences": "Artskart", "environment": "MykoKnoks"},
    }
    one = build_dataset_manifest(
        **kwargs,
        presence_cells=["p2", "p1"],
        background_cells=["b2", "b1"],
    )
    two = build_dataset_manifest(
        **kwargs,
        presence_cells=["p1", "p2", "p1"],
        background_cells=["b1", "b2"],
    )

    assert one["dataset_sha256"] == two["dataset_sha256"]
    assert one["dataset_id"] == two["dataset_id"]
    assert one["calibrated"] is False
    assert one["core"]["presence_cells"] == ["p1", "p2"]
