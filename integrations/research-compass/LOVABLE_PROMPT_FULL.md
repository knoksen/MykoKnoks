Paste everything below the line into the Lovable chat for the Research Compass project.

---

Add a private, reviewer-only import of the MykoKnoks research-bank seed. Use the three files at the end of this message exactly as written; do not rewrite their logic.

1. Database: apply `supabase/migrations/20260923080000_research_import.sql` as a migration. Keep every constraint, the trigger and all row-level security policies. Do not add any policy for `anon`.
2. Edge function: create `import-research-seed` from `supabase/functions/import-research-seed/index.ts` and `validate.ts`. It needs `SUPABASE_URL`, `SUPABASE_ANON_KEY` and `SUPABASE_SERVICE_ROLE_KEY`, which Lovable Cloud already provides. Keep JWT verification on.
3. Screen (inside the existing workspace/admin area and design system): add a page at `/admin/research-imports`, only reachable when signed in, and hide it from navigation for everyone without the editor or administrator role (use the existing `has_role`).
   - A button **Import latest seed** that calls the edge function with `supabase.functions.invoke('import-research-seed', { body: {} })`, plus an optional field for a specific 40-character commit SHA.
   - A list of batches: date, dataset version, short commit SHA linking to the commit on GitHub, row count, status, and any validation errors.
   - For the selected batch, a table of proposals: scientific name (italic), taxonomic status, Norway evidence status, evidence grade, a badge when `changed_since_last_review` is true, and **Approve** / **Reject** buttons with an optional note. Show the full `original` JSON in an expandable row.
   - Approved rows get a separate **Publish** toggle. Leave it off by default.
4. Do not change the existing public `/mykoknoks` page, and do not show any imported data publicly. Publishing is a separate decision.
5. Wording on the screen: "Imported rows are proposals from the versioned seed. They are not confirmed occurrences."


## Files

### `supabase/migrations/20260923080000_research_import.sql`

```sql
-- Research Compass: private staging for MykoKnoks research-bank imports.
-- Everything here is reviewer-only. Nothing is readable by anonymous visitors,
-- and nothing is published until a reviewer approves it and a separate public
-- view is created (see "Publishing" at the end).

-- Reviewers are the project's existing editors and administrators
-- (public.user_roles / public.has_role from the base migration).
create or replace function public.is_research_reviewer()
returns boolean language sql stable security definer set search_path = public as $$
  select public.has_role(auth.uid(), 'editor') or public.has_role(auth.uid(), 'administrator');
$$;

create table if not exists public.research_import_batches (
  id uuid primary key default gen_random_uuid(),
  source_repo text not null,
  commit_sha text not null check (commit_sha ~ '^[0-9a-f]{40}$'),
  file_path text not null,
  payload_sha256 text not null check (payload_sha256 ~ '^[0-9a-f]{64}$'),
  dataset_id text,
  dataset_version text,
  dataset_as_of date,
  retrieved_at timestamptz not null,
  status text not null check (status in ('awaiting_review', 'reviewed', 'rejected', 'failed')),
  row_count integer not null default 0,
  errors jsonb,
  raw_payload jsonb,
  program_slug text not null default 'mykoknoks',
  imported_by uuid references auth.users (id),
  created_at timestamptz not null default now(),
  unique (commit_sha, file_path)
);

create table if not exists public.research_taxon_proposals (
  id uuid primary key default gen_random_uuid(),
  batch_id uuid not null references public.research_import_batches (id) on delete cascade,
  scientific_name text not null,
  taxonomic_status text not null,
  norway_evidence_status text not null,
  evidence_grade text not null,
  original jsonb not null,                -- the row exactly as the seed had it
  changed_since_last_review boolean,      -- null when never reviewed before
  review_state text not null default 'proposed'
    check (review_state in ('proposed', 'approved', 'rejected')),
  review_note text,
  reviewed_by uuid references auth.users (id),
  reviewed_at timestamptz,
  published boolean not null default false,
  created_at timestamptz not null default now(),
  unique (batch_id, scientific_name),
  -- a row can only be published after approval
  check (not published or review_state = 'approved')
);

-- The original values are an audit record: they can never be edited.
create or replace function public.research_proposals_guard()
returns trigger language plpgsql as $$
begin
  if new.original is distinct from old.original
     or new.scientific_name is distinct from old.scientific_name
     or new.batch_id is distinct from old.batch_id then
    raise exception 'Imported values are read-only; import a new batch instead';
  end if;
  if old.review_state <> 'proposed' and new.review_state = 'proposed' then
    raise exception 'A reviewed row cannot be reset to proposed';
  end if;
  if new.review_state <> old.review_state then
    new.reviewed_by := auth.uid();
    new.reviewed_at := now();
  end if;
  return new;
end $$;

drop trigger if exists research_proposals_guard on public.research_taxon_proposals;
create trigger research_proposals_guard before update on public.research_taxon_proposals
  for each row execute function public.research_proposals_guard();

alter table public.research_import_batches enable row level security;
alter table public.research_taxon_proposals enable row level security;

-- Reviewers read everything and review proposals. Inserts come only from the
-- edge function (service role), which bypasses RLS.
create policy "reviewers read batches" on public.research_import_batches
  for select to authenticated using (public.is_research_reviewer());
create policy "reviewers read proposals" on public.research_taxon_proposals
  for select to authenticated using (public.is_research_reviewer());
create policy "reviewers review proposals" on public.research_taxon_proposals
  for update to authenticated using (public.is_research_reviewer()) with check (public.is_research_reviewer());

create index if not exists research_proposals_batch_idx on public.research_taxon_proposals (batch_id);
create index if not exists research_proposals_name_idx on public.research_taxon_proposals (scientific_name, reviewed_at desc);

-- Publishing: deliberately not created here. When Jarle decides to publish,
-- add a view over approved + published rows that exposes only public fields
-- (never raw_payload, reviewer ids, or any locality), and grant select on that
-- view to anon.

-- Access: any user with the editor or administrator role in public.user_roles
-- can import and review. No extra setup is needed.
```

### `supabase/functions/import-research-seed/validate.ts`

```ts
// Pure validation for the MykoKnoks research-bank seed, per
// docs/RESEARCH_COMPASS_INTEGRATION.md ("Import contract").
// No I/O here, so it can be unit-tested outside Deno.

export type SeedTaxon = {
  scientific_name: string;
  rank: string;
  taxonomic_status: string;
  norway_evidence_status: string;
  evidence_grade: string;
  research_note: string;
  source_urls: string[];
  family?: string;
  gbif_taxon_key?: number | null;
  artsdatabanken_taxon_id?: number | null;
  ncbi_taxid?: number | null;
  species_fungorum_id?: string | null;
  historical_names?: string[];
};

export type Seed = {
  dataset: { id: string; version: string; as_of: string; scientific_boundary: string[] };
  taxa: SeedTaxon[];
};

export type ValidationResult =
  | { ok: true; seed: Seed }
  | { ok: false; errors: string[] };

const REQUIRED = [
  "scientific_name",
  "rank",
  "taxonomic_status",
  "norway_evidence_status",
  "evidence_grade",
  "research_note",
  "source_urls",
] as const;

export function validateSeed(input: unknown, expectedDatasetId?: string): ValidationResult {
  const errors: string[] = [];
  if (!input || typeof input !== "object" || Array.isArray(input)) {
    return { ok: false, errors: ["Top level must be a JSON object"] };
  }
  const doc = input as Record<string, unknown>;
  const dataset = doc.dataset as Record<string, unknown> | undefined;
  if (!dataset || typeof dataset !== "object") errors.push("Missing dataset object");
  else {
    for (const k of ["id", "version", "as_of"]) {
      if (typeof dataset[k] !== "string" || !(dataset[k] as string).trim()) errors.push(`dataset.${k} must be a non-empty string`);
    }
    if (!Array.isArray(dataset.scientific_boundary) || dataset.scientific_boundary.length === 0) {
      errors.push("dataset.scientific_boundary must be a non-empty list");
    }
    // "exactly one origin dataset ID": the file declares one id, and it must be the one we expect.
    if (expectedDatasetId && dataset.id !== expectedDatasetId) {
      errors.push(`dataset.id is '${String(dataset.id)}', expected '${expectedDatasetId}'`);
    }
  }
  if (!Array.isArray(doc.taxa) || doc.taxa.length === 0) {
    errors.push("taxa must be a non-empty list");
    return { ok: false, errors };
  }
  const seen = new Set<string>();
  (doc.taxa as unknown[]).forEach((raw, i) => {
    const where = `taxa[${i}]`;
    if (!raw || typeof raw !== "object") { errors.push(`${where} is not an object`); return; }
    const t = raw as Record<string, unknown>;
    for (const k of REQUIRED) if (!(k in t)) errors.push(`${where}: missing ${k}`);
    const name = typeof t.scientific_name === "string" ? t.scientific_name.trim() : "";
    if (!name) errors.push(`${where}: scientific_name must be a non-empty string`);
    else if (seen.has(name.toLowerCase())) errors.push(`${where}: duplicate scientific_name '${name}'`);
    else seen.add(name.toLowerCase());
    if (t.rank !== "species") errors.push(`${where} (${name}): rank must be 'species'`);
    if (typeof t.research_note !== "string" || !t.research_note.trim()) errors.push(`${where} (${name}): research_note is empty`);
    if (!Array.isArray(t.source_urls) || t.source_urls.length === 0) errors.push(`${where} (${name}): source_urls is empty`);
    else for (const u of t.source_urls) {
      try {
        const url = new URL(String(u));
        if (url.protocol !== "https:") errors.push(`${where} (${name}): source is not HTTPS: ${u}`);
      } catch { errors.push(`${where} (${name}): invalid URL: ${u}`); }
    }
    if (t.historical_names !== undefined && !Array.isArray(t.historical_names)) errors.push(`${where} (${name}): historical_names must be a list`);
    // Coordinates never belong in the taxonomy seed; refuse anything that looks like one.
    for (const k of Object.keys(t)) {
      if (/^(lat|lon|lng|latitude|longitude|coordinates?|geometry|decimal(lat|long))/i.test(k)) {
        errors.push(`${where} (${name}): field '${k}' looks like a locality and is not allowed in the seed`);
      }
    }
  });
  return errors.length ? { ok: false, errors } : { ok: true, seed: input as Seed };
}

export async function sha256Hex(text: string): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}
```

### `supabase/functions/import-research-seed/index.ts`

```ts
// Supabase Edge Function: import the MykoKnoks research-bank seed into
// Research Compass as private, unpublished proposals.
//
// Contract (docs/RESEARCH_COMPASS_INTEGRATION.md):
// - fetched server-side, pinned to a commit SHA
// - JSON shape, HTTPS sources, unique names and one dataset id are validated
// - raw payload hash, version, retrieval time, commit SHA and each row's
//   original values are stored
// - reviewed rows are never overwritten; a changed upstream row becomes a new
//   proposal in a new batch
//
// Callers must be signed in with the editor or administrator role.
// No Notion token or service-role key ever reaches the browser.

import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.4";
import { sha256Hex, validateSeed } from "./validate.ts";

const REPO = "knoksen/MykoKnoks";
const SEED_PATH = "data/research-bank/taxonomy-psilocybe-nordic-v1.json";
const EXPECTED_DATASET_ID = "mykoknoks-nordic-psilocybe-seed-v1";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { ...cors, "Content-Type": "application/json" } });

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return json(405, { error: "Use POST" });

  const url = Deno.env.get("SUPABASE_URL")!;
  const anon = Deno.env.get("SUPABASE_ANON_KEY")!;
  const service = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
  const authHeader = req.headers.get("Authorization") ?? "";

  // 1. Who is asking, and are they a reviewer?
  const asUser = createClient(url, anon, { global: { headers: { Authorization: authHeader } } });
  const { data: userData, error: userErr } = await asUser.auth.getUser();
  if (userErr || !userData?.user) return json(401, { error: "Sign in first" });
  const admin = createClient(url, service);
  const { data: isReviewer } = await asUser.rpc("is_research_reviewer");
  if (!isReviewer) return json(403, { error: "Only editors and administrators can import" });

  // 2. Pin to a commit: use the one asked for, or resolve main's current head.
  let body: { commit_sha?: string } = {};
  try { body = await req.json(); } catch { /* empty body is fine */ }
  const gh = { "Accept": "application/vnd.github+json", "User-Agent": "research-compass-import" };
  let sha = (body.commit_sha ?? "").trim();
  if (sha && !/^[0-9a-f]{40}$/i.test(sha)) return json(400, { error: "commit_sha must be a full 40-character SHA" });
  if (!sha) {
    const r = await fetch(`https://api.github.com/repos/${REPO}/commits/main`, { headers: gh });
    if (!r.ok) return json(502, { error: `GitHub commit lookup failed (${r.status})` });
    sha = (await r.json()).sha;
  }

  // 3. Idempotent: the same file at the same commit is imported once.
  const { data: existing } = await admin
    .from("research_import_batches").select("id, status, row_count")
    .eq("commit_sha", sha).eq("file_path", SEED_PATH).maybeSingle();
  if (existing) return json(200, { batch_id: existing.id, commit_sha: sha, already_imported: true, ...existing });

  // 4. Fetch the raw file at that exact commit.
  const raw = await fetch(`https://raw.githubusercontent.com/${REPO}/${sha}/${SEED_PATH}`);
  if (!raw.ok) return json(502, { error: `Could not fetch seed at ${sha} (${raw.status})` });
  const text = await raw.text();
  const payloadHash = await sha256Hex(text);
  const retrievedAt = new Date().toISOString();

  let parsed: unknown;
  try { parsed = JSON.parse(text); } catch { return json(422, { error: "Seed is not valid JSON" }); }
  const check = validateSeed(parsed, EXPECTED_DATASET_ID);
  if (!check.ok) {
    await admin.from("research_import_batches").insert({
      source_repo: REPO, commit_sha: sha, file_path: SEED_PATH, payload_sha256: payloadHash,
      retrieved_at: retrievedAt, status: "rejected", row_count: 0, errors: check.errors,
      imported_by: userData.user.id,
    });
    return json(422, { error: "Seed failed validation", details: check.errors });
  }
  const seed = check.seed;

  // 5. Store the batch and every row as a private proposal with its original values.
  const { data: batch, error: bErr } = await admin.from("research_import_batches").insert({
    source_repo: REPO, commit_sha: sha, file_path: SEED_PATH, payload_sha256: payloadHash,
    dataset_id: seed.dataset.id, dataset_version: seed.dataset.version, dataset_as_of: seed.dataset.as_of,
    retrieved_at: retrievedAt, status: "awaiting_review", row_count: seed.taxa.length,
    raw_payload: parsed, imported_by: userData.user.id,
  }).select("id").single();
  if (bErr) return json(500, { error: bErr.message });

  // Compare with the latest reviewed decision per name, so the reviewer sees what changed.
  const { data: reviewed } = await admin
    .from("research_taxon_proposals").select("scientific_name, original, review_state, reviewed_at")
    .in("review_state", ["approved", "rejected"]).order("reviewed_at", { ascending: false });
  const lastReviewed = new Map<string, Record<string, unknown>>();
  for (const r of reviewed ?? []) if (!lastReviewed.has(r.scientific_name)) lastReviewed.set(r.scientific_name, r.original);

  const rows = seed.taxa.map((t) => {
    const prev = lastReviewed.get(t.scientific_name);
    return {
      batch_id: batch.id,
      scientific_name: t.scientific_name,
      taxonomic_status: t.taxonomic_status,
      norway_evidence_status: t.norway_evidence_status,
      evidence_grade: t.evidence_grade,
      original: t,
      changed_since_last_review: prev ? JSON.stringify(prev) !== JSON.stringify(t) : null,
      review_state: "proposed",
      published: false,
    };
  });
  const { error: rErr } = await admin.from("research_taxon_proposals").insert(rows);
  if (rErr) {
    await admin.from("research_import_batches").update({ status: "failed", errors: [rErr.message] }).eq("id", batch.id);
    return json(500, { error: rErr.message });
  }
  return json(201, {
    batch_id: batch.id, commit_sha: sha, payload_sha256: payloadHash, dataset_version: seed.dataset.version,
    rows: rows.length, changed_since_last_review: rows.filter((r) => r.changed_since_last_review).length,
  });
});
```
