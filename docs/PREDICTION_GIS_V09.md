# MykoKnoks v0.9 — Prediction GIS Engine

v0.9 converts the ecological GIS from visual context into explicit, machine-readable H3 evidence.

## Scope

- normalise AR5, SR16 and NGU WMS feature evidence into stable scalar/categorical features;
- preserve raw evidence/provenance separately from model features;
- expose score decomposition and feature coverage per H3 cell;
- add optional Artskart occurrence context without treating missing observations as absence;
- persist normalised GIS vectors in the lightweight SQLite/PostgreSQL H3 store;
- keep the model explicitly heuristic until spatial cross-validation and probability calibration are available.

## Prediction endpoint

`GET /api/v1/prediction/cells` builds on the existing H3 grid and MET weather pipeline. Live mode normalises WMS evidence at each H3 cell. Store mode reads the same feature vector from the H3 feature store. Responses include `gis_features`, `score_components`, `model_profile`, provenance and interpretation warnings.

The current taxon-specific profile is deliberately narrow: `Psilocybe semilanceata` receives an explicit open-land/moisture heuristic profile because the legacy baseline was already designed around that ecology. Other taxa retain the generic legacy habitat score until a defensible taxon-specific profile or trained model exists.

## Artskart semantics

Artskart is presence-only, observer-biased occurrence evidence. The endpoint may inspect a bounded nearby sample and reports matching records separately in metadata. A zero match is explicitly **not** treated as absence evidence and does not reduce the cell score.

## Feature store

The lightweight store adds `gis_features_json`. `init_lite_feature_store.py` performs an additive migration for existing Ultra SQLite databases, so older stores can be upgraded without dropping the current H3 rows.

## Scientific guardrail

The output remains an ecological suitability index, not a calibrated species-occurrence probability. Before probability semantics are introduced, MykoKnoks still needs occurrence/background sampling, spatial cross-validation, model registry/versioning, calibration and external validation.
