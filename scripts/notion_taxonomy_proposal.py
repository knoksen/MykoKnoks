#!/usr/bin/env python3
"""Turn a Notion taxonomy snapshot into a reviewable research-bank proposal.

Input is a raw export of the Notion "Nordic Mycology — Taxonomy" data source
(rows exactly as Notion returned them). Output is:

* a proposal file with one row per Notion taxon, mapped to the seed vocabulary
  but with every original Notion value kept alongside, and
* a Markdown diff report against the current versioned seed.

Nothing here edits the seed. Per docs/RESEARCH_COMPASS_INTEGRATION.md a
reviewer must approve each change before a new seed version is cut.

Usage:
    python scripts/notion_taxonomy_proposal.py SNAPSHOT.json --retrieved-at 2026-09-23T06:05:00Z
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "data" / "research-bank"
SEED = BANK / "taxonomy-psilocybe-nordic-v1.json"
NOTION_DATA_SOURCE = "collection://0f95fe95-8f11-4dae-bf79-d7814cc2b30b"
NOTION_DATABASE_URL = "https://app.notion.com/p/360b160674404028804e582adba1dd1f"

STATUS_MAP = {
    "Confirmed": "confirmed",
    "Established": "established",
    "Historical": "historical",
    "Conflicted": "conflicted",
    "Unverified": "unverified",
    "No evidence found": "no_evidence_found",
    "Cultivation-related": "cultivation_related",
}
# The v1 seed uses finer-grained states. These are the coarse Notion states
# each seed state is compatible with, so a difference is only reported when
# the two sources genuinely disagree.
SEED_STATUS_FAMILY = {
    "established": {"established", "confirmed"},
    "historical_revised_material": {"historical"},
    "historical_material_needs_revision": {"historical", "unverified"},
    "conflicted": {"conflicted"},
    "unverified_wild_occurrence": {"unverified", "cultivation_related"},
    "cultivation_related": {"cultivation_related"},
}


def split_names(value: str | None) -> list[str]:
    return [n.strip() for n in (value or "").split(";") if n.strip()]


def as_int(value) -> int | None:
    return int(value) if isinstance(value, (int, float)) else None


def map_row(row: dict) -> dict:
    grade_label = row.get("Evidence grade") or ""
    status_label = row.get("Norway evidence status") or ""
    source = row.get("Source")
    return {
        "scientific_name": row["Name"].strip(),
        "rank": (row.get("Rank") or "").lower() or None,
        "family": row.get("Family") or None,
        "genus": row.get("Genus") or None,
        "taxonomic_status": (row.get("Taxonomic status") or "").lower() or None,
        "norway_evidence_status": STATUS_MAP.get(status_label, None),
        "evidence_grade": grade_label[:1] or None,
        "gbif_taxon_key": as_int(row.get("GBIF key")),
        "artsdatabanken_taxon_id": as_int(row.get("Artsdatabanken ID")),
        "ncbi_taxid": as_int(row.get("NCBI TaxID")),
        "species_fungorum_id": row.get("Species Fungorum ID") or None,
        "historical_names": split_names(row.get("Historical names")),
        "research_note": row.get("Notes") or "",
        "source_urls": [source] if source else [],
        "nordic_status": json.loads(row.get("Nordic status") or "[]"),
        "last_reviewed": row.get("date:Last reviewed:start"),
        "review_state": "proposed",
        "provenance": {
            "notion_page_url": row.get("url"),
            "original": {k: v for k, v in row.items() if k != "url"},
        },
    }


def row_flags(p: dict) -> list[str]:
    flags = []
    if p["rank"] != "species":
        flags.append(f"rank is '{p['rank']}': the v1 seed schema only accepts species")
    if p["norway_evidence_status"] is None:
        flags.append("Norway evidence status is missing or not a known option")
    if not p["source_urls"]:
        flags.append("no source URL")
    for url in p["source_urls"]:
        if not url.startswith("https://"):
            flags.append(f"source is not HTTPS: {url}")
        if "artsdatabanken.no/taxon/" in url:
            flags.append("source uses the old artsdatabanken.no/taxon URL form, which the 2026-09-16 audit found broken")
    if p["taxonomic_status"] in {"synonym", "unresolved"}:
        flags.append(f"taxonomic status is '{p['taxonomic_status']}': keep as crosswalk, do not count as a separate occurrence")
    return flags


def compare(seed_row: dict, p: dict) -> list[str]:
    out = []
    if seed_row["evidence_grade"][:1] != (p["evidence_grade"] or ""):
        out.append(f"evidence grade: seed **{seed_row['evidence_grade']}**, Notion **{p['evidence_grade']}**")
    fam = SEED_STATUS_FAMILY.get(seed_row["norway_evidence_status"], {seed_row["norway_evidence_status"]})
    if p["norway_evidence_status"] not in fam:
        out.append(f"Norway status: seed `{seed_row['norway_evidence_status']}`, Notion `{p['norway_evidence_status']}`")
    for key in ("gbif_taxon_key", "artsdatabanken_taxon_id", "ncbi_taxid", "species_fungorum_id"):
        a, b = seed_row.get(key), p.get(key)
        if a is not None and b is not None and str(a) != str(b):
            out.append(f"{key}: seed `{a}`, Notion `{b}`")
        elif a is not None and b is None:
            out.append(f"{key}: seed has `{a}`, Notion is empty")
        elif a is None and b is not None:
            out.append(f"{key}: Notion adds `{b}`")
    missing_hist = sorted(set(seed_row.get("historical_names", [])) - set(p["historical_names"]))
    if missing_hist:
        out.append("historical names in seed but not in Notion: " + ", ".join(f"*{n}*" for n in missing_hist))
    new_hist = sorted(set(p["historical_names"]) - set(seed_row.get("historical_names", [])))
    if new_hist:
        out.append("historical names Notion adds: " + ", ".join(f"*{n}*" for n in new_hist))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("snapshot", type=Path)
    ap.add_argument("--retrieved-at", required=True, help="ISO 8601 time the Notion rows were read")
    ap.add_argument("--out-dir", type=Path, default=BANK / "proposals")
    args = ap.parse_args()

    raw_bytes = args.snapshot.read_bytes()
    raw = json.loads(raw_bytes)
    rows = raw["results"]
    day = args.retrieved_at[:10]
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    seed_by_name = {t["scientific_name"]: t for t in seed["taxa"]}

    proposals = sorted((map_row(r) for r in rows), key=lambda p: p["scientific_name"])
    names = [p["scientific_name"] for p in proposals]
    if len(names) != len(set(names)):
        raise SystemExit("Duplicate scientific names in the Notion snapshot")

    for p in proposals:
        p["flags"] = row_flags(p)
        s = seed_by_name.get(p["scientific_name"])
        p["seed_comparison"] = {"in_seed_v1": s is not None, "differences": compare(s, p) if s else []}

    args.out_dir.mkdir(parents=True, exist_ok=True)
    snap_path = args.out_dir / f"notion-taxonomy-{day}.snapshot.json"
    snap_path.write_bytes(raw_bytes)
    doc = {
        "proposal": {
            "id": f"notion-taxonomy-{day}",
            "status": "awaiting_review",
            "source": {"system": "notion", "data_source": NOTION_DATA_SOURCE, "database_url": NOTION_DATABASE_URL},
            "retrieved_at": args.retrieved_at,
            "snapshot_file": snap_path.name,
            "snapshot_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "base_seed": {"file": SEED.name, "id": seed["dataset"]["id"], "version": seed["dataset"]["version"]},
            "rules": [
                "Every row is a proposal. Nothing here changes the versioned seed.",
                "Original Notion values are kept under provenance.original for audit.",
                "A reviewer approves or rejects each row before a new seed version is cut.",
                "Variety-level and synonym rows are crosswalk entries, not additional occurrences.",
            ],
        },
        "taxa": proposals,
    }
    prop_path = args.out_dir / f"notion-taxonomy-{day}.proposal.json"
    prop_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    only_seed = sorted(set(seed_by_name) - set(names))
    in_both = [p for p in proposals if p["seed_comparison"]["in_seed_v1"]]
    new = [p for p in proposals if not p["seed_comparison"]["in_seed_v1"]]
    lines = [
        f"# Notion → seed review, {day}",
        "",
        f"Snapshot of Notion *Nordic Mycology — Taxonomy* read at {args.retrieved_at} "
        f"({len(rows)} rows, SHA-256 `{doc['proposal']['snapshot_sha256'][:16]}…`), compared with "
        f"`{SEED.name}` v{seed['dataset']['version']} ({len(seed['taxa'])} taxa).",
        "",
        "Nothing in this report changes the seed. Each item needs a reviewer decision.",
        "",
        f"## Taxa in both ({len(in_both)})",
        "",
    ]
    for p in in_both:
        diffs = p["seed_comparison"]["differences"]
        lines.append(f"### *{p['scientific_name']}*")
        lines += [f"- {d}" for d in diffs] if diffs else ["- No disagreement beyond wording."]
        lines += [f"- ⚠ {f}" for f in p["flags"]]
        lines.append("")
    lines += [f"## In Notion only ({len(new)})", "", "Candidates for a later seed version. None are occurrence evidence by themselves.", "",
              "| Taxon | Rank | Taxonomic status | Norway status | Grade | Flags |", "|---|---|---|---|---|---|"]
    for p in new:
        lines.append(f"| *{p['scientific_name']}* | {p['rank']} | {p['taxonomic_status']} | {p['norway_evidence_status']} | {p['evidence_grade']} | {'; '.join(p['flags']) or '–'} |")
    lines += ["", f"## In seed only ({len(only_seed)})", ""]
    lines += [f"- *{n}* — not found in Notion; check whether it was renamed or dropped." for n in only_seed] or ["- None."]
    report = ROOT / "docs" / "proposals" / f"NOTION_TAXONOMY_REVIEW_{day}.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(proposals)} proposals → {prop_path.relative_to(ROOT)}\nreport → {report.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
