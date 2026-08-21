# MykoKnoks v0.2 data pipeline

## Principle

Interactive forecasts should not hammer public OGC services. MykoKnoks therefore separates:

1. **Live probe** — inspect a coordinate against current upstream services.
2. **Ingestion** — extract environmental evidence over H3 cells in controlled batches.
3. **Feature store** — persist normalized H3 features in PostGIS/Parquet.
4. **Model training** — join occurrence dates and coordinates to environmental/weather features.
5. **Serving** — read precomputed features and model outputs at low latency.

## Norway source stack

| Layer | Primary source | v0.2 path |
|---|---|---|
| Occurrences | Artsdatabanken Artskart / Artsobservasjoner | API adapter + export script |
| Forecast weather | MET Norway Locationforecast 2.0 | live API |
| Elevation / terrain | Kartverket / Geonorge elevation WPS | live + ingestion |
| Land resources | NIBIO AR5 | WMS discovery + feature-info probe |
| Forest | NIBIO SR16 | WMS discovery + feature-info probe |
| Quaternary geology | NGU Løsmasser | WMS discovery + feature-info probe |
| Vegetation | Sentinel-2 L2A | Copernicus STAC adapter |

## Feature-store target

One H3 row should carry values plus provenance, acquisition timestamp, source version and
quality/completeness fields. Raw upstream evidence is retained separately so derived features
can be regenerated without silently losing lineage.

## Model validation

Random train/test splits are not sufficient for spatial ecology. Use spatial blocks or grouped
H3 parents to reduce spatial leakage. Metrics should include ROC-AUC/PR-AUC, calibration,
spatial holdout performance and uncertainty, not only a single accuracy score.
