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
