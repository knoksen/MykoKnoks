"""Resumable H3 ingestion for a supplied national/region GeoJSON boundary.

The operator supplies an authoritative Polygon/MultiPolygon boundary. MykoKnoks does
not ship a hand-drawn Norway outline. Jobs can be sharded deterministically and resumed.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import get_settings  # noqa: E402
from app.services.features import LiveNorwayFeatureService  # noqa: E402
from app.services.grid import cell_center, cell_geometry  # noqa: E402


def _geometry_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    kind = payload.get("type")
    if kind == "FeatureCollection":
        return [
            feature["geometry"]
            for feature in payload.get("features", [])
            if isinstance(feature, dict) and isinstance(feature.get("geometry"), dict)
        ]
    if kind == "Feature" and isinstance(payload.get("geometry"), dict):
        return [payload["geometry"]]
    if kind in {"Polygon", "MultiPolygon"}:
        return [payload]
    raise ValueError("Boundary must be GeoJSON Polygon, MultiPolygon, Feature, or FeatureCollection")


def cells_from_boundary(boundary: Path, resolution: int) -> list[str]:
    import h3

    payload = json.loads(boundary.read_text(encoding="utf-8"))
    cells: set[str] = set()
    for geometry in _geometry_items(payload):
        cells.update(h3.geo_to_cells(geometry, resolution))
    return sorted(cells)


def completed_cells(path: Path) -> set[str]:
    if not path.exists():
        return set()
    completed: set[str] = set()
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            cell = row.get("h3")
            if cell:
                completed.add(str(cell))
    return completed


async def run(args: argparse.Namespace) -> None:
    if args.shard_index < 0 or args.shard_index >= args.shard_count:
        raise ValueError("shard-index must be in [0, shard-count)")

    cells = cells_from_boundary(args.boundary, args.resolution)
    cells = [
        cell
        for index, cell in enumerate(cells)
        if index % args.shard_count == args.shard_index
    ]
    if args.max_cells:
        cells = cells[: args.max_cells]

    output = args.out
    output.parent.mkdir(parents=True, exist_ok=True)
    already = completed_cells(output) if args.resume else set()
    pending = [cell for cell in cells if cell not in already]

    print(
        f"boundary_cells={len(cells)} completed={len(already)} pending={len(pending)} "
        f"resolution={args.resolution} shard={args.shard_index}/{args.shard_count}"
    )
    if args.dry_run:
        return

    settings = get_settings()
    service = LiveNorwayFeatureService(settings)
    semaphore = asyncio.Semaphore(max(1, args.concurrency))

    async def fetch(cell: str) -> dict[str, Any]:
        lon, lat = cell_center(cell)
        async with semaphore:
            snapshot = await service.probe(
                lat,
                lon,
                include_wms=True,
                include_terrain_metrics=not args.no_terrain_metrics,
            )
        return {
            "h3": cell,
            "geometry": cell_geometry(cell),
            "snapshot": snapshot.model_dump(),
            "resolution": args.resolution,
            "feature_version": "model-platform-v1.0",
        }

    mode = "a" if args.resume and output.exists() else "w"
    with output.open(mode, encoding="utf-8") as handle:
        for start in range(0, len(pending), args.batch_size):
            batch_cells = pending[start : start + args.batch_size]
            rows = await asyncio.gather(*(fetch(cell) for cell in batch_cells))
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            handle.flush()
            done = min(start + len(batch_cells), len(pending))
            print(f"wrote={done}/{len(pending)} file={output}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--boundary", type=Path, required=True)
    parser.add_argument("--resolution", type=int, default=9)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--max-cells", type=int)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-terrain-metrics", action="store_true")
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
