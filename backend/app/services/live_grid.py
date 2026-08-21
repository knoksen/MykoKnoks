from __future__ import annotations

import asyncio

from app.schemas import EnvironmentalSnapshot
from app.services.features import LiveNorwayFeatureService
from app.services.grid import cell_center


async def probe_cells(
    cells: list[str],
    service: LiveNorwayFeatureService,
    concurrency: int = 8,
) -> dict[str, EnvironmentalSnapshot]:
    """Probe real elevation/terrain per cell with bounded upstream concurrency.

    Full AR5/SR16/NGU extraction belongs in the persisted feature-store ingestion pipeline;
    the live map path intentionally avoids hammering WMS services.
    """
    semaphore = asyncio.Semaphore(max(1, concurrency))

    async def one(cell: str) -> tuple[str, EnvironmentalSnapshot]:
        lon, lat = cell_center(cell)
        async with semaphore:
            snapshot = await service.probe(lat, lon, include_wms=False)
        return cell, snapshot

    results = await asyncio.gather(*(one(cell) for cell in cells))
    return dict(results)
