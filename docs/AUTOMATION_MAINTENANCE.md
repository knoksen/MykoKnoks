# MykoKnoks maintenance and automation register

Updated 2026-09-23. This is the operational coverage map. A scheduled check is not a live data connector, and no research claim is auto-approved.

| Function | Update trigger | Automated control | Human decision / current gap |
|---|---|---|---|
| GitHub code and tests | Every push and pull request | Existing `CI` runs backend tests, lint, build and sample data checks | Review failing CI before merge |
| Taxonomy and media research seed | Every push/PR; Monday 06:15 UTC | `CI` and `research-bank-maintenance` run `validate_research_bank.py` | Resolve disputed taxonomy and source provenance in Notion; no automatic grade elevation |
| Research Compass export | Monday 06:15 UTC; manual workflow dispatch | Maintenance workflow verifies exact Git commit, digest package shape, idempotent keys and unpublished status | Private server import and editor review in Lovable remain unimplemented because workspace editing was credit-blocked |
| Notion evidence and task register | Weekly connected-app review | ChatGPT scheduled maintenance review checks dated tasks, reconciliation flags and changes against the GitHub seed | Notion is the editorial workspace; source-level corrections require review; no two-way sync |
| NotebookLM reading notebook | Manual source import on version change | Weekly review compares its listed GitHub source references to repo documentation and flags stale snapshots | Google Notebook currently has no connector here; notebook source updates cannot be promised as automatic |
| Lovable Research Compass | Weekly connected-app review | Check project build state, publication state and connector configuration; report changes and failed controls | Build server-side import, RLS review queue and publication gate when workspace can edit |
| Google AI Studio BioBuild Evidence Lab | Manual cross-project review when material claims are proposed | No scheduled import; inspect cited source before any transfer | Separate biological-material research app, not an occurrence register; claims remain unverified |
| External taxonomy / voucher / occurrence sources | When source changes or a review task opens | Record original URL, retrieval date, source version and claim-level differences in Notion | Do not infer wild occurrence from taxon pages, photos or cultivated material; exact sensitive localities remain private |
| Habitat model and maps | Every push/PR via existing CI smoke checks | Reproducible synthetic pipeline tests candidate manifests and keeps `calibrated: false` boundary | Scientific calibration, licenses, spatial generalization and publication need explicit review |

## Failure path

1. A failing GitHub workflow is visible in repository Actions. Preserve its logs and source commit; fix the underlying data or code, then rerun. The scheduled job does not deploy or publish.
2. A weekly connected-app review records the affected function, last known successful check, evidence link, owner and next action in the Notion task register. Never silently mark unavailable app checks as passing.
3. Any upstream source revision becomes a new proposal keyed to dataset version and commit. Keep prior determinations and reviewer decisions; do not overwrite approved history.
4. If a connector is unavailable, report the gap. A link or a browser session does not provide continuous synchronization.

## Coverage gate for new functions

Before shipping a new feature, specify: source of truth, event or cadence, automated validation, freshness threshold, error signal, owner, recovery procedure and publication boundary. Add a CI or scheduled check where the feature can safely run without external credentials. Track integrations separately from code validation.
