# Research Compass handoff

The offline exporter `scripts/export_research_compass.py` creates a **private review proposal** from the eight-taxon MykoKnoks seed. It does not authenticate to Notion or Research Compass and does not publish anything.

Example from a checkout at the exact source commit:

```bash
python scripts/validate_research_bank.py
python scripts/export_research_compass.py --commit "$(git rev-parse HEAD)" --output research-compass-proposal.json
```

The exporter records the SHA declared by the caller, but **does not verify** that the input bytes came from that commit. Its `commit_verified: false` field is deliberate. Before ingestion, the receiving service must fetch `data/research-bank/taxonomy-psilocybe-nordic-v1.json` at `declared_commit_sha`, compare SHA-256 with `payload_sha256`, and reject a mismatch. It must enforce editor authorization and private row-level security on the server. Use `proposal_key` as the idempotency key, preserve the original row and review decision, and create a new proposal for a changed version. Nothing in this package is a verified wild occurrence.

## Research Compass work remaining

1. Add an authenticated server-side import action with the immutable-fetch and digest check above.
2. Add a private staging table with unique `proposal_key`, source metadata, raw row, state and audit history. Apply and test RLS so public and non-editor users cannot read or approve proposals.
3. Add a Norwegian/English editor review screen displaying source links and the unresolved reconciliation flags in `docs/RESEARCH_COMPASS_INTEGRATION.md`.
4. Require a specific evidence review and license/locality check before copying any approved content to public research pages. Keep suitability and occurrence distinct.
5. Test duplicate import, payload mismatch, rejected URL, non-editor approval, public read, and review audit trail before enabling connector state.

As of 2026-09-23, Lovable's workspace reported no remaining credits for code edits. No Research Compass import, automatic Notion sync, or publication is live. This document is a handoff for completing the application work when editing becomes available.
