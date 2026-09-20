#!/usr/bin/env python3
"""Dependency-free integrity checks for curated MykoKnoks research-bank seeds."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "data" / "research-bank"


def load(name: str) -> dict:
    with (BANK / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def require_url(value: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"Expected public HTTPS URL, got {value!r}")


def main() -> None:
    taxonomy = load("taxonomy-psilocybe-nordic-v1.json")
    media = load("media-psilocybe-v1.json")

    taxa = taxonomy["taxa"]
    names = [row["scientific_name"] for row in taxa]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate scientific_name in taxonomy seed")

    required_taxon_fields = {
        "scientific_name",
        "rank",
        "taxonomic_status",
        "norway_evidence_status",
        "evidence_grade",
        "research_note",
        "source_urls",
    }
    for row in taxa:
        missing = sorted(required_taxon_fields - row.keys())
        if missing:
            raise ValueError(f"{row.get('scientific_name', '<unknown>')}: missing {missing}")
        if row["rank"] != "species":
            raise ValueError(f"{row['scientific_name']}: unsupported rank")
        if not row["source_urls"]:
            raise ValueError(f"{row['scientific_name']}: source_urls is empty")
        for url in row["source_urls"]:
            require_url(url)

    media_rows = media["media"]
    media_names = [row["scientific_name"] for row in media_rows]
    if len(media_names) != len(set(media_names)):
        raise ValueError("Duplicate scientific_name in media manifest")
    if set(media_names) != set(names):
        raise ValueError("Taxonomy/media scientific_name sets differ")

    for row in media_rows:
        require_url(row["source_page"])
        if row["role"] != "visual_reference":
            raise ValueError(f"{row['scientific_name']}: invalid media role")
        if row["occurrence_evidence"] or row["identification_evidence"]:
            raise ValueError(f"{row['scientific_name']}: visual reference promoted to evidence")

    print(f"Research bank validated: {len(taxa)} taxa, {len(media_rows)} media records")


if __name__ == "__main__":
    main()
