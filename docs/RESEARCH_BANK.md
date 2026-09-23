# Research bank

This directory connects the operational MykoKnoks platform to the curated Nordic mycology research workflow.

## Notion research workspace

The [Nordic Mycology Research Hub](https://app.notion.com/p/3dbfe29092ad81a18b8ff0ae6586c0ea) holds the working source registry, verification queue, occurrence and evidence records, taxonomy crosswalk, and research tasks. The [2015 baseline working page](https://app.notion.com/p/3ddfe29092ad8119b196fab31a7f9aa0) tracks the unresolved historical eight-species count.

Notion is the review workspace; `data/research-bank/` is the versioned, validated seed consumed by code. Changes between them require a documented source, retrieval date, original and accepted names, evidence rationale, and a review of location and image licensing. A link between records does not imply automatic synchronization or upgrade a candidate occurrence to verified status.

## Contents

- `taxonomy-psilocybe-nordic-v1.json` — eight priority taxa with explicit Norwegian evidence states, identifiers, historical names and source links.
- `taxonomy-record.schema.json` — machine-readable validation contract.
- `media-psilocybe-v1.json` — image provenance and licence manifest.

## Evidence model

| Grade | Meaning |
|---|---|
| A | Verified voucher, sequence or direct expert confirmation with traceable provenance |
| B | Authoritative database and/or primary literature |
| C | Conflicted or incomplete evidence requiring primary-source or voucher audit |
| D | Community/discovery lead; not verified occurrence evidence |
| E | Historical record requiring modern revision |
| F | Rejected or superseded identification retained for audit history |

A grade describes the evidence supporting the stated claim. It is not a score for how visually convincing a photograph appears.

## Non-negotiable scientific rules

1. Keep reported, candidate and verified taxon names separate.
2. Never infer Norwegian occurrence from a taxon-registry entry alone.
3. Never infer absence from a missing occurrence record.
4. Preserve original labels and later determinations as an audit trail.
5. Treat photographs as visual references unless they are explicitly bound to an observation and reviewed evidence package.
6. Keep cultivation-related observations separate from wild occurrence.
7. Keep sensitive exact locations out of public exports.
8. Version every dataset and retain source URLs, retrieval dates and transformation history.

## 2015 baseline limitation

The public Nortaxa/Artsnavnebasen IPT history currently begins with version 1.2 dated 2020-09-23. That version reports 209,888 records, but its DwC-A file was not archived. A public 2014–2016 dataset snapshot is therefore not available from the current IPT archive. The 2015 eight-species count remains a reconstruction problem until the data owner supplies a historical extract or equivalent primary evidence.

## Integration direction

The seed is deliberately independent of prediction code. A future taxonomy resolver should consume these records and expose:

- reported name;
- accepted name;
- determination qualifier such as `cf.`;
- evidence state and grade;
- voucher/provenance links;
- taxonomic history;
- public-location policy.

Prediction, occurrence and taxonomy layers must remain separable so a modelled suitable cell can never be mistaken for a verified record.
