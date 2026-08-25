"""Ingest nearby Artskart presence-only records into the portable warehouse."""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.clients.artskart import ArtskartClient, web_mercator_bbox_wkt  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.repositories.occurrence_store import (  # noqa: E402
    OccurrenceStoreRepository,
    extract_records,
    normalize_occurrence,
)


async def run(args: argparse.Namespace) -> None:
    settings = get_settings()
    client = ArtskartClient(settings.upstream_timeout_seconds)
    repository = OccurrenceStoreRepository(settings.database_url)
    repository.initialize()

    radius_m = max(100.0, args.radius_km * 1000.0)
    polygon = web_mercator_bbox_wkt(args.lat, args.lon, radius_m)
    written = 0

    for page in range(args.max_pages):
        payload = await client.observations(
            {
                "gmWktPolygon": polygon,
                "pageSize": args.page_size,
                "page": page,
            }
        )
        raw_records = extract_records(payload)
        if not raw_records:
            break

        records = [
            normalize_occurrence(
                record,
                source_id="artskart",
                h3_resolution=args.resolution,
            )
            for record in raw_records
        ]
        if args.species:
            needle = args.species.casefold()
            records = [
                record
                for record in records
                if record.scientific_name and needle in record.scientific_name.casefold()
            ]

        written += repository.upsert_many(records)
        print(
            f"page={page} fetched={len(raw_records)} stored={len(records)} total={written}"
        )
        if len(raw_records) < args.page_size:
            break

    print(f"warehouse_rows={repository.count()} inserted_or_updated={written}")
    print("Presence-only records are not absence data and require spatial-bias handling in SDM training.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--radius-km", type=float, default=5.0)
    parser.add_argument("--species")
    parser.add_argument("--resolution", type=int, default=9)
    parser.add_argument("--page-size", type=int, default=128, choices=range(1, 129), metavar="1..128")
    parser.add_argument("--max-pages", type=int, default=20)
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
