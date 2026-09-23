#!/usr/bin/env python3
"""Build a private, review-only Research Compass import proposal from the seed.

No network access or credentials are needed. This command never imports or publishes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_SEED = Path(__file__).resolve().parents[1] / "data/research-bank/taxonomy-psilocybe-nordic-v1.json"
SHA_RE = re.compile(r"[0-9a-f]{40}\Z")
VERSION_RE = re.compile(r"\d+\.\d+\.\d+\Z")
BLOCKED_STATUSES = {
    "conflicted", "historical_material_needs_revision", "unverified_wild_occurrence",
    "cultivation_related", "historical_revised_material",
}


def proposal(raw: bytes, commit: str) -> dict:
    if not SHA_RE.fullmatch(commit):
        raise ValueError("--commit must be a full lowercase 40-character Git commit SHA")
    data = json.loads(raw)
    if not isinstance(data, dict) or not isinstance(data.get("dataset"), dict):
        raise ValueError("Missing dataset metadata")
    metadata, taxa = data["dataset"], data.get("taxa")
    dataset_id, version = metadata.get("id"), metadata.get("version")
    if not isinstance(dataset_id, str) or not dataset_id or not isinstance(version, str) or not VERSION_RE.fullmatch(version):
        raise ValueError("Dataset ID and semantic version are required")
    if not isinstance(taxa, list) or not taxa:
        raise ValueError("Expected nonempty taxa array")
    digest = hashlib.sha256(raw).hexdigest()
    seen, records = set(), []
    for row in taxa:
        if not isinstance(row, dict):
            raise ValueError("Each taxon must be an object")
        name = row.get("scientific_name")
        if not isinstance(name, str) or not name.startswith("Psilocybe ") or name in seen:
            raise ValueError(f"Invalid or duplicate scientific name: {name!r}")
        seen.add(name)
        if row.get("rank") != "species" or row.get("taxonomic_status") != "accepted":
            raise ValueError(f"{name}: unsupported rank or taxonomic status")
        status, grade, sources = row.get("norway_evidence_status"), row.get("evidence_grade"), row.get("source_urls")
        if not isinstance(status, str) or not status or not isinstance(grade, str) or not grade:
            raise ValueError(f"{name}: missing evidence status or grade")
        if not isinstance(sources, list) or not sources:
            raise ValueError(f"{name}: sources are required")
        for url in sources:
            if not isinstance(url, str) or urlparse(url).scheme != "https" or not urlparse(url).netloc:
                raise ValueError(f"{name}: invalid source URL")
        if not isinstance(row.get("research_note"), str) or not row["research_note"]:
            raise ValueError(f"{name}: research note is required")
        key = hashlib.sha256(f"{dataset_id}\0{version}\0{commit}\0{name}".encode()).hexdigest()
        records.append({
            "proposal_key": key,
            "review_state": "pending",
            "publication_state": "unpublished",
            "claim_type": "taxon_research_lead",
            "wild_occurrence_verified": False,
            "review_flags": (["evidence_reconciliation_required"] if status in BLOCKED_STATUSES else []),
            "source_record": row,
        })
    return {
        "schema_version": "1.0.0",
        "kind": "mykoknoks_research_compass_import_proposal",
        "visibility": "private",
        "source": {
            "repository": "knoksen/MykoKnoks",
            "path": "data/research-bank/taxonomy-psilocybe-nordic-v1.json",
            "declared_commit_sha": commit,
            "commit_verified": False,
            "payload_sha256": digest,
            "dataset_id": dataset_id,
            "dataset_version": version,
            "dataset_as_of": metadata.get("as_of"),
        },
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True, help="Immutable commit containing the exact input bytes")
    parser.add_argument("--input", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = proposal(args.input.read_bytes(), args.commit)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(result['records'])} private review proposals to {args.output}")


if __name__ == "__main__":
    main()
