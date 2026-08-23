# MykoKnoks v1.0 — Nordic fungal model platform

v1.0 promotes MykoKnoks from a GIS heuristic workbench to an auditable modelling platform while keeping the scientific boundary explicit.

## What is production in v1.0

- H3 environmental feature store with normalized AR5, SR16 and NGU vectors.
- Optional five-point Kartverket elevation stencil producing local slope and roughness.
- MET Locationforecast timeline with transparent decaying precipitation-memory features.
- Presence-only Artskart occurrence warehouse with raw payload preservation and H3 indexing.
- Explicit model registry distinguishing production heuristics from untrained/training candidates.
- Resumable and deterministic national/region H3 ingestion driven by an operator-supplied authoritative GeoJSON boundary.
- Spatially grouped cross-validation training pipeline with dataset hash, fold metrics and model manifest.

## Scientific boundary

The built-in `semilanceata-gis-heuristic-v1` model remains an explainable ecological suitability index. It is not a calibrated occurrence probability and is not species-identification or edibility advice.

The `fungal-sdm-spatial-cv-v1-candidate` registry entry is a training contract, not a trained model. A generated candidate manifest remains `calibrated: false` until a separate probability-calibration stage and independent spatial validation are completed.

Artskart is presence-only evidence. No record in a query is not absence evidence. Training datasets must explicitly construct defensible background/pseudo-absence samples and control spatial sampling bias.

## Rainfall memory

The v1 temporal engine derives 24 h, 72 h and 168 h precipitation totals plus an exponentially decaying moisture-memory index from the available MET forecast timeline. `memory_coverage_hours` and `memory_quality` expose warm-up limitations. The current implementation does not claim observed rainfall before the first timeline timestamp.

## Terrain metrics

Full ingestion can sample centre, north, south, east and west elevations from Kartverket. A local gradient produces slope in degrees and the five-point elevation standard deviation is stored as terrain roughness. Interactive detailed live GIS is deliberately capped; bulk feature extraction belongs in the persisted H3 ingestion pipeline.

## National ingestion

`scripts/ingest_national_h3.py` requires an authoritative GeoJSON Polygon/MultiPolygon. The repository intentionally does not ship a hand-drawn Norway outline. Jobs support deterministic shards, resume mode, bounded concurrency, dry-run and maximum-cell safety limits.

Example dry run:

```bash
python scripts/ingest_national_h3.py \
  --boundary data/norway-authoritative.geojson \
  --resolution 9 \
  --out data/norway-r9-shard-0.jsonl \
  --shard-count 16 \
  --shard-index 0 \
  --dry-run
```

## Occurrence warehouse

`scripts/ingest_artskart_occurrences.py` pages through a bounded nearby Artskart query and normalizes stable record identifiers, scientific name, timestamp, WGS84 coordinates, uncertainty, H3 cell, source payload hash and full raw JSON.

## Spatial model training

`ml/train_spatial_cv.py` consumes a prepared labelled CSV with the v1 feature contract and a spatial-block column. It uses `StratifiedGroupKFold`, writes fold-level ROC AUC / average precision / Brier score, hashes the input dataset and persists both a Joblib artifact and JSON model manifest.

The training pipeline does not automatically make the resulting probabilities calibrated.

## Release criterion

A future model may be promoted from `candidate` only after:

1. data provenance and feature versions are frozen;
2. occurrence/background sampling is documented;
3. spatial CV is completed without spatial leakage;
4. an independent holdout region or time period is evaluated;
5. probability calibration is measured separately;
6. the model manifest and metrics are registered and reproducible.
