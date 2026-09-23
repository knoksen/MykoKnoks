# MykoKnoks ↔ Research Compass data contract

Updated: 2026-09-23. This contract joins three existing surfaces without treating a link as a live connector.

| Surface | Role | Address |
|---|---|---|
| Notion Nordic Mycology Research Hub | Working source, taxonomy, evidence and review records | https://app.notion.com/p/3dbfe29092ad81a18b8ff0ae6586c0ea |
| MykoKnoks GitHub | Versioned, machine-readable research seed | https://github.com/knoksen/MykoKnoks/tree/main/data/research-bank |
| Jarlhalla Research Compass | Private editorial staging and later reviewed public presentation | https://lovable.dev/projects/0472d1a2-39c5-4a8c-a9cd-ec80100199e9 |
| NotebookLM | Optional source reading and research notes; homepage link only, no specific notebook or synchronization configured | https://notebook.google.com/ |

## Import contract

The public seed `taxonomy-psilocybe-nordic-v1.json` is an import **proposal**, not confirmed occurrences. Fetch server-side at a recorded commit SHA, validate the JSON shape, HTTPS sources, unique scientific names and exactly one origin dataset ID. Store the raw payload hash, version, retrieved time, commit SHA and each row's original values. Never overwrite a reviewed record because upstream changes; create a new proposal or diff.

Import begins private and unpublished. A reviewer must inspect source URLs, historical names, current taxonomic treatment, voucher/sequence provenance, license and locality policy before promoting a row. Do not infer wild Norwegian presence from a registry page, photo, modelled habitat, or a cultivated record. No exact sensitive coordinates go into public exports.

Notion is not publicly readable by the app and is not automatically synchronized. Export from Notion requires a separately scoped connection and a field-by-field review. Never place a Notion token or service-role key in client code.

## Reconciliation checkpoint

The GitHub seed contains eight priority taxa; Notion Taxonomy contains a broader 25-row working register. The seed does not represent the report's unresolved historical eight-species list. As of the 2026-09-23 comparison:

- `P. silvatica`: GitHub seed grade C and historical-material status; Notion taxon row grade D and Unverified. Voucher-level records in Notion also have their own grades. Do not flatten these different claim levels into one score.
- `P. fimetaria`: GitHub says unverified wild occurrence; Notion marks the located Norwegian record cultivation-related. Keep wild occurrence unverified, exclude cultivated material from a wild checklist.
- `P. cyanescens` / `P. arcana` / `P. serbica var. arcana`: maintain historical and current names plus the `cf.` determination on O:F:177904; do not double count.
- `P. pelliculosa`: pre-2015 Norwegian provenance and specimen-specific sequence remain unresolved.
- The baseline report's Artsnavnebase snapshot date is 2015-04-27. The currently public IPT history does not provide that snapshot.

These are review flags, not automatic corrections to the seed. Preserve the 2026-09-20 dataset until a sourced revision is approved and versioned.

## Acceptance gates

1. Import uses an immutable source commit and idempotent key; repeated runs create no duplicate proposals.
2. An unauthenticated user cannot read staged payloads or invoke ingestion; authorization is enforced server-side and by RLS.
3. An authenticated non-editor cannot approve or publish a proposal.
4. Candidate data never silently appears as a verified finding.
5. Every approved change has reviewer, time, source, old value and new value.
6. Public map output is generalized and distinguishes suitability from presence.
7. UI explains the current connector state truthfully and supports Norwegian and English.
