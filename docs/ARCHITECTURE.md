# Architecture

## Design principles

1. Separate **habitat suitability** from **fruiting conditions**.
2. Preserve provenance: source, acquisition date, version and transformation metadata.
3. Validate models spatially; random row splits exaggerate skill with autocorrelated ecological data.
4. Protect sensitive locations and private observations.
5. Prefer open standards: GeoJSON, COG, STAC, OGC APIs, GeoParquet, H3 and PMTiles.

## Target production pipeline

```text
Artskart / GBIF -------> occurrence lake -------+
NIBIO AR5/SR16 -------> environmental features  |
Kartverket DTM --------> terrain features         |--> H3 feature store --> SDM --+
NGU geology -----------> substrate features      |                              |
Sentinel-2 -----------> EO features -------------+                              |
                                                                                +--> Forecast API --> MapLibre PWA
MET forecast ----------> temporal features ------------------------------------+
MET historical --------> lagged weather ---------------------------------------+
```

Default display/feature grid is H3 resolution 9. Original observations and rasters remain at native resolution; H3 is an indexing/analysis layer, not a statement that every input has ~0.1 km² precision.

## Model evolution

- v0.1: transparent heuristic + live weather + synthetic habitat demo.
- v0.2: real H3 environmental feature store and occurrence ingestion.
- v0.3: species-specific gradient boosting SDM with spatial block validation.
- v0.4: temporal fruiting model with lagged weather.
- v0.5: calibrated uncertainty, ensemble models and observation feedback.

Each prediction should expose habitat score, fruiting score, combined score, confidence, model version and top drivers.
