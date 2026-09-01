from __future__ import annotations

from dataclasses import dataclass

from app.repositories.occurrence_store import NormalizedOccurrence


@dataclass(frozen=True)
class OccurrenceQualityResult:
    records: list[NormalizedOccurrence]
    rejected_wrong_taxon: int
    rejected_invalid_coordinate: int
    rejected_uncertainty: int
    rejected_duplicate_event: int


def _event_key(record: NormalizedOccurrence) -> tuple[str, str, float, float]:
    return (
        (record.scientific_name or "").casefold(),
        record.observed_at or "",
        round(float(record.lat), 5),
        round(float(record.lon), 5),
    )


def filter_occurrences(
    records: list[NormalizedOccurrence],
    *,
    species: str,
    max_coordinate_uncertainty_m: float | None = 1000.0,
) -> OccurrenceQualityResult:
    """Apply explicit, conservative filters to presence-only occurrence records.

    Unknown coordinate uncertainty is retained rather than silently treated as precise.
    Duplicate event detection uses taxon + timestamp + coordinates rounded to about metre
    scale and keeps the lexicographically first stable source record ID.
    """
    target = species.strip().casefold()
    accepted: list[NormalizedOccurrence] = []
    wrong_taxon = 0
    invalid_coordinate = 0
    uncertainty = 0
    duplicates = 0
    seen: set[tuple[str, str, float, float]] = set()

    for record in sorted(records, key=lambda item: item.source_record_id):
        if not record.scientific_name or record.scientific_name.casefold() != target:
            wrong_taxon += 1
            continue
        if (
            record.lat is None
            or record.lon is None
            or record.h3 is None
            or not -90 <= record.lat <= 90
            or not -180 <= record.lon <= 180
        ):
            invalid_coordinate += 1
            continue
        if (
            max_coordinate_uncertainty_m is not None
            and record.coordinate_uncertainty_m is not None
            and record.coordinate_uncertainty_m > max_coordinate_uncertainty_m
        ):
            uncertainty += 1
            continue

        key = _event_key(record)
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        accepted.append(record)

    return OccurrenceQualityResult(
        records=accepted,
        rejected_wrong_taxon=wrong_taxon,
        rejected_invalid_coordinate=invalid_coordinate,
        rejected_uncertainty=uncertainty,
        rejected_duplicate_event=duplicates,
    )
