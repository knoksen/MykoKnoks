"""Build a real-data JSONL H3 feature snapshot around one coordinate.

This deliberately separates slow upstream extraction from low-latency map serving.
Example:
  python scripts/ingest_live_features.py --lat 58.735 --lon 5.647 --radius-km 1 --out data/jaren.jsonl
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import get_settings  # noqa: E402
from app.services.features import LiveNorwayFeatureService  # noqa: E402
from app.services.grid import cell_center, cell_geometry, cells_around  # noqa: E402


async def run(args: argparse.Namespace) -> None:
    settings = get_settings()
    service = LiveNorwayFeatureService(settings)
    cells = cells_around(args.lat, args.lon, args.radius_km, args.resolution)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(args.concurrency)

    async def fetch(cell: str) -> dict:
        lon, lat = cell_center(cell)
        async with semaphore:
            snapshot = await service.probe(lat, lon, include_wms=not args.fast)
        return {
            "h3": cell,
            "geometry": cell_geometry(cell),
            "snapshot": snapshot.model_dump(),
            "resolution": args.resolution,
            "feature_version": "prediction-gis-v0.9",
        }

    with output.open("w", encoding="utf-8") as handle:
        for start in range(0, len(cells), args.batch_size):
            batch = await asyncio.gather(*(fetch(cell) for cell in cells[start : start + args.batch_size]))
            for row in batch:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"wrote {min(start + args.batch_size, len(cells))}/{len(cells)} cells")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--radius-km", type=float, default=1.0)
    parser.add_argument("--resolution", type=int, default=9)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--fast", action="store_true", help="Skip WMS probes; elevation/terrain only")
    parser.add_argument("--out", default="data/live_features.jsonl")
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
