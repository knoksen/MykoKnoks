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
