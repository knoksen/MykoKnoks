"""Small Artskart API exporter for reproducible occurrence pulls.

The script intentionally accepts raw API query parameters because Artskart exposes many
filters and the exact scientific filtering strategy should be recorded per model run.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.clients.artskart import ArtskartClient  # noqa: E402


async def run(args: argparse.Namespace) -> None:
    params: dict[str, str | int | float] = {}
    for item in args.param:
        key, sep, value = item.partition("=")
        if not sep:
            raise SystemExit(f"Invalid --param {item!r}; expected key=value")
        params[key] = value
    payload = await ArtskartClient(args.timeout).observations(params)
    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved Artskart response to {args.out}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--param", action="append", default=[])
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--out", default="data/artskart.json")
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
