from __future__ import annotations

import json
from dataclasses import dataclass
from math import exp
from typing import Any


@dataclass(frozen=True)
class OccurrenceContext:
    species: str
    records_examined: int
    matching_records: int
    support_index: float
    interpretation: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "species": self.species,
            "records_examined": self.records_examined,
            "matching_records": self.matching_records,
            "support_index": round(self.support_index, 4),
            "interpretation": self.interpretation,
        }


def _record_list(payload: dict | list | None) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    for key in ("items", "records", "observations", "data", "results"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return [payload]


def occurrence_context(payload: dict | list | None, species: str) -> OccurrenceContext:
    records = _record_list(payload)
    needle = species.strip().casefold()
    matches = 0
    for record in records:
        text = json.dumps(record, ensure_ascii=False, default=str).casefold()
        if needle and needle in text:
            matches += 1

    support = 0.0 if matches <= 0 else 1.0 - exp(-matches / 3.0)
    interpretation = (
        "Nearby Artskart records support local observation context; presence-only data are not a probability."
        if matches
        else "No matching record was found in the inspected sample; this is not absence evidence."
    )
    return OccurrenceContext(
        species=species,
        records_examined=len(records),
        matching_records=matches,
        support_index=support,
        interpretation=interpretation,
    )
