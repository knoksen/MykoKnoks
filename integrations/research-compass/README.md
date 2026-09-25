# Research Compass import (Lovable)

Brings the versioned MykoKnoks seed into Jarlhalla Research Compass as private proposals, following the import contract in [`docs/RESEARCH_COMPASS_INTEGRATION.md`](../../docs/RESEARCH_COMPASS_INTEGRATION.md).

```
GitHub seed @ commit SHA ──► edge function import-research-seed ──► research_import_batches
                              (server side, validates, hashes)        research_taxon_proposals (proposed, unpublished)
                                                                         │ reviewer approves / rejects
                                                                         ▼
                                                               later: public view of approved rows
```

## What is enforced

| Rule from the contract | Where |
|---|---|
| Fetched server-side at a recorded commit SHA | `index.ts` resolves `main` to a full SHA, then reads `raw.githubusercontent.com/<repo>/<sha>/…` |
| JSON shape, HTTPS sources, unique names, one dataset id | `validate.ts` (tested against the v1 seed and a broken copy) |
| Store payload hash, version, retrieval time, SHA, original row values | `research_import_batches`, `research_taxon_proposals.original` |
| Never overwrite a reviewed record | Same SHA + file is imported once; `original` is read-only (trigger); a reviewed row can't be reset |
| Import starts private and unpublished | RLS: editors and administrators only (existing `has_role`), no anon access; `published` requires `approved` (check constraint) |
| No sensitive coordinates | `validate.ts` refuses any lat/lon/geometry field in the seed |
| No keys in client code | The service role is used only inside the edge function |

## Install

1. In Lovable, open the Research Compass project and paste the prompt from `LOVABLE_PROMPT.md` into the chat. It asks Lovable to add the migration, the edge function and a reviewer screen using these exact files.
2. Open the new *Research imports* screen and press **Import latest seed**.

Tested here: `validate.ts` against the real seed and a deliberately broken one; the migration's constraints, trigger and row-level security in Postgres (PGlite) with a reviewer and a non-reviewer.
Not tested here: the edge function end to end, since that needs the project's Supabase instance.
