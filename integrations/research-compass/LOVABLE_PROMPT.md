Paste everything below the line into the Lovable chat for the Research Compass project.

---

Add a private, reviewer-only import of the MykoKnoks research-bank seed. Use the files from https://github.com/knoksen/MykoKnoks/tree/main/integrations/research-compass exactly as written; do not rewrite their logic.

1. Database: apply `supabase/migrations/20260923080000_research_import.sql` as a migration. Keep every constraint, the trigger and all row-level security policies. Do not add any policy for `anon`.
2. Edge function: create `import-research-seed` from `supabase/functions/import-research-seed/index.ts` and `validate.ts`. It needs `SUPABASE_URL`, `SUPABASE_ANON_KEY` and `SUPABASE_SERVICE_ROLE_KEY`, which Lovable Cloud already provides. Keep JWT verification on.
3. Screen (inside the existing workspace/admin area and design system): add a page at `/admin/research-imports`, only reachable when signed in, and hide it from navigation for everyone without the editor or administrator role (use the existing `has_role`).
   - A button **Import latest seed** that calls the edge function with `supabase.functions.invoke('import-research-seed', { body: {} })`, plus an optional field for a specific 40-character commit SHA.
   - A list of batches: date, dataset version, short commit SHA linking to the commit on GitHub, row count, status, and any validation errors.
   - For the selected batch, a table of proposals: scientific name (italic), taxonomic status, Norway evidence status, evidence grade, a badge when `changed_since_last_review` is true, and **Approve** / **Reject** buttons with an optional note. Show the full `original` JSON in an expandable row.
   - Approved rows get a separate **Publish** toggle. Leave it off by default.
4. Do not change the existing public `/mykoknoks` page, and do not show any imported data publicly. Publishing is a separate decision.
5. Wording on the screen: "Imported rows are proposals from the versioned seed. They are not confirmed occurrences."
