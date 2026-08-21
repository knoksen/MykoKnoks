# Architecture

## Design goals

MykoKnoks is built around reproducibility, spatial lineage, explicit uncertainty and low-latency serving. Public geodata services are treated as upstream evidence providers, not as a runtime database for every map pan.

## Runtime paths

### Demo mode

Deterministic H3 placeholders exercise the complete UI/API path without claiming ecological validity.

### Live mode

The API performs a bounded number of Kartverket elevation/terrain point queries. This is useful for validation and demonstrations. Live mode is intentionally capped to avoid abusive fan-out against public services.

### Feature-store mode

Production serving reads normalized H3 features from PostGIS. Cells absent from the store are clearly marked as fallback/synthetic instead of silently pretending to contain real measurements.

## Ingestion path

```text
OGC/API/STAC source
      │
      ▼
source-specific adapter
      │
      ▼
raw evidence + source metadata
      │
      ├────────► env_feature_evidence
      │
      ▼
normalization / aggregation
      │
      ▼
H3 env_features
      │
      ├────────► model training
      └────────► low-latency API serving
```

## Why H3

H3 provides stable cell identifiers, hierarchical spatial grouping, neighbourhood operations and a convenient bridge between raster, vector, occurrence and model-output datasets. It also supports spatial-block validation by grouping fine cells into coarser parents.

## Why retain raw evidence

A derived field such as `soil_moisture_proxy=0.78` is not self-explanatory. The platform stores the underlying source payload, acquisition time and source id separately so normalization logic can be audited and rerun.

## Production constraints

- Use batch/bulk downloads where providers recommend them.
- Cache capabilities and metadata.
- Rate-limit live probes.
- Record source licenses and attribution.
- Do not expose sensitive occurrence coordinates for rare/protected taxa without a privacy policy.
- Do not train/evaluate spatial models with naive random splits alone.
