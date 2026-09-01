# MykoKnoks v1.1 — Validated Habitat Intelligence

v1.1 converts the v1.0 modelling infrastructure into a reproducible real-data habitat-SDM workflow. It does **not** promote heuristic suitability to calibrated occurrence probability.

## Milestone 1 — Reproducible dataset foundation ✅

Implemented on `v1.1-validated-habitat`:

- deterministic H3 background sampling with explicit seed
- presence-cell and near-presence H3 buffer exclusion
- spatial parent-stratum balancing so dense local candidate clusters do not dominate
- exact-taxon occurrence filtering
- coordinate and uncertainty quality gates
- duplicate event filtering by taxon + timestamp + rounded coordinate
- training CSV generation from complete `env_features` vectors only
- stable dataset SHA-256 identity from species, feature contract, selected H3 cells, sampling policy and source metadata
- manifest guardrail: `calibrated: false`
- CI system test covering warehouse → H3 store → sampler → training CSV → manifest

### Scientific semantics

Artskart records are presence-only. A selected background H3 cell is a sampling control for classifier mechanics and is never asserted to be a biological absence. Unknown coordinate uncertainty is retained and remains distinguishable from known precise coordinates. A model must pass spatial validation and a separate probability-calibration gate before any UI/API may label its output an occurrence probability.

## Jæren pilot workflow

1. Back up the production feature store.
2. Ingest a bounded, authoritative Jæren pilot polygon into H3 resolution 9 with full AR5/SR16/NGU/terrain extraction.
3. Ingest Artskart occurrence records for the target species into `occurrence_records`.
4. Build the reproducible dataset:

```bash
python scripts/build_validated_habitat_dataset.py \
  --database ~/.local/share/mykoknoks/features.sqlite \
  --species 'Psilocybe semilanceata' \
  --out-dir data/datasets/semilanceata-jaeren-v11 \
  --background-ratio 3 \
  --seed 20260901 \
  --buffer-rings 1 \
  --stratum-resolution 6 \
  --block-resolution 6 \
  --max-uncertainty-m 1000
```

The output directory contains `habitat-training.csv` and `dataset-manifest.json`.

## Milestone 2 — Spatial model validation ✅

Implemented:

- Logistic Regression baseline
- Random Forest candidate
- HistGradientBoosting candidate
- one materialized `StratifiedGroupKFold` partition set reused by all candidates
- per-fold test-group SHA-256 signatures proving identical spatial partitions
- ROC-AUC, PR-AUC, Brier score and log loss per fold
- mean, variance, minimum and maximum summaries for each metric
- benchmark-only ranking; no automatic production promotion
- nested spatial calibration evaluation with inner grouped calibration folds and outer spatial holdouts
- internal Brier/log-loss calibration gate plus 10-bin ECE diagnostic
- model-agnostic permutation importance on grouped spatial holdout folds
- explicit distinction between feature sensitivity and causal attribution
- CI gate covering benchmark, calibration evaluation and feature-importance guardrails

Hard scientific flags remain:

- `calibrated: false`
- `probability_claim_allowed: false`
- `independent_validation_completed: false`

Even a passing internal calibration gate is not independent validation and does not unlock occurrence-probability language.

## Milestone 3 — Real Forecast 🚧

Next work:

1. spatial MET weather sampling across the loaded H3 area instead of one center-point forecast
2. bounded cache and rate limiting for upstream weather requests
3. observed antecedent-rainfall provider contract kept separate from forecast-timeline memory
4. explicit habitat × temporal component scoring
5. temporal H3 rendering/day slider and selected-cell sparkline
6. data-quality labels replacing ambiguous confidence terminology

## Release boundary

v1.1 remains a candidate release until the forecast milestone, production migration, Windows/Android gates and release documentation are complete. Probability language remains disabled until independent validation and an explicit production calibration gate exist.
