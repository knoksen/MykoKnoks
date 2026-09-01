from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass

import h3


@dataclass(frozen=True)
class BackgroundSampleResult:
    cells: list[str]
    candidate_count: int
    excluded_presence_count: int
    excluded_buffer_count: int
    strata_count: int
    seed: int


def _valid_cells(cells: list[str]) -> list[str]:
    return sorted({str(cell) for cell in cells if cell and h3.is_valid_cell(str(cell))})


def _presence_buffer(presence_cells: list[str], rings: int) -> set[str]:
    if rings < 0:
        raise ValueError("buffer_rings must be >= 0")
    buffered: set[str] = set()
    for cell in _valid_cells(presence_cells):
        buffered.update(h3.grid_disk(cell, rings))
    return buffered


def sample_background_cells(
    candidate_cells: list[str],
    presence_cells: list[str],
    *,
    sample_size: int,
    seed: int = 20260901,
    buffer_rings: int = 1,
    stratum_resolution: int = 6,
) -> BackgroundSampleResult:
    """Select deterministic spatially distributed background H3 cells.

    Background is a classifier sampling role only; selected cells are never asserted
    biological absences. Presence cells and an H3 ring buffer around them are excluded.
    Remaining candidates are grouped by a coarser H3 parent and sampled round-robin
    across strata so dense local candidate clusters do not dominate the background set.
    """
    if sample_size < 1:
        raise ValueError("sample_size must be >= 1")

    candidates = _valid_cells(candidate_cells)
    presences = set(_valid_cells(presence_cells))
    if not candidates:
        return BackgroundSampleResult([], 0, 0, 0, 0, seed)

    candidate_resolution = h3.get_resolution(candidates[0])
    if any(h3.get_resolution(cell) != candidate_resolution for cell in candidates):
        raise ValueError("candidate_cells must use one H3 resolution")
    if stratum_resolution < 0 or stratum_resolution > candidate_resolution:
        raise ValueError("stratum_resolution must be between 0 and candidate resolution")

    buffer = _presence_buffer(list(presences), buffer_rings)
    excluded_presence = sum(cell in presences for cell in candidates)
    excluded_buffer = sum(cell in buffer and cell not in presences for cell in candidates)
    eligible = [cell for cell in candidates if cell not in buffer]

    strata: dict[str, list[str]] = defaultdict(list)
    for cell in eligible:
        parent = h3.cell_to_parent(cell, stratum_resolution)
        strata[parent].append(cell)

    rng = random.Random(seed)
    for cells in strata.values():
        rng.shuffle(cells)

    stratum_keys = sorted(strata)
    rng.shuffle(stratum_keys)
    selected: list[str] = []
    while stratum_keys and len(selected) < sample_size:
        next_round: list[str] = []
        for key in stratum_keys:
            cells = strata[key]
            if cells and len(selected) < sample_size:
                selected.append(cells.pop())
            if cells:
                next_round.append(key)
        stratum_keys = next_round

    return BackgroundSampleResult(
        cells=sorted(selected),
        candidate_count=len(candidates),
        excluded_presence_count=excluded_presence,
        excluded_buffer_count=excluded_buffer,
        strata_count=len(strata),
        seed=seed,
    )
