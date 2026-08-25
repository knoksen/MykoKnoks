from __future__ import annotations

import asyncio

from app.schemas import EnvironmentalSnapshot
from app.services.features import LiveNorwayFeatureService
from app.services.grid import cell_center


async def probe_cells(
    cells: list[str],
    service: LiveNorwayFeatureService,
    concurrency: int = 8,
    *,
    include_wms: bool = False,
    include_terrain_metrics: bool = False,
) -> dict[str, EnvironmentalSnapshot]:
    """Probe environmental evidence per H3 cell with bounded upstream concurrency.

    The interactive default remains lightweight. Detailed WMS + terrain-gradient probing
    is opt-in because it multiplies upstream requests and belongs primarily in ingestion.
    """
    semaphore = asyncio.Semaphore(max(1, concurrency))

    async def one(cell: str) -> tuple[str, EnvironmentalSnapshot]:
        lon, lat = cell_center(cell)
        async with semaphore:
            snapshot = await service.probe(
                lat,
                lon,
                include_wms=include_wms,
                include_terrain_metrics=include_terrain_metrics,
            )
        return cell, snapshot

    results = await asyncio.gather(*(one(cell) for cell in cells))
    return dict(results)
