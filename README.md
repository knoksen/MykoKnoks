# MykoKnoks

**Nordic ecological intelligence engine** — an auditable geospatial platform for fungal habitat and fruiting forecasts, Norway first.

MykoKnoks separates two ecological questions:

1. **WHERE?** Habitat suitability from occurrences, terrain, land resources, forest, geology and vegetation.
2. **WHEN?** Fruiting potential from recent/forecast weather and eventually lagged historical weather.

The platform never treats a coloured map cell as proof that a species is present.

## v0.2 — Real Norway Data Engine

v0.2 adds an operational data architecture around the original MVP:

- FastAPI API with `demo`, bounded `live` and PostGIS `store` forecast modes.
- H3 spatial grid with provenance and confidence on every forecast cell.
- MET Norway Locationforecast integration.
- Kartverket/Geonorge elevation + terrain WPS client.
- NIBIO AR5 and SR16 WMS capability discovery + point feature-info probing.
- NGU Løsmasser WMS capability discovery + point feature-info probing.
- Artsdatabanken Artskart occurrence/taxonomy adapter and export CLI.
- Copernicus Sentinel-2 STAC adapter.
- Controlled H3 environmental ingestion to JSONL.
- PostGIS loader retaining both normalized features and raw source evidence.
- Database lineage tables for sources, ingestion runs and model runs.
- React/TypeScript/MapLibre PWA with data-mode controls and source/provenance UI.
- Spatially grouped ML baseline code.
- Docker Compose and GitHub Actions CI.

## Architecture

```text
                          ┌──────────────────────────────┐
Artskart / occurrences ──►│ occurrence warehouse         │
                          └──────────────┬───────────────┘
                                         │
Kartverket terrain ─┐                    │
NIBIO AR5/SR16 ─────┼──► H3 ingestion ──┼──► PostGIS feature store
NGU geology ─────────┤       + lineage    │             │
Sentinel-2 ──────────┘                    │             │
                                         ▼             ▼
                                   spatial ML/SDM   FastAPI
MET forecast/history ─────────────► temporal model      │
                                                       ▼
                                               MapLibre React PWA
```

## API

### Metadata and source discovery

- `GET /health`
- `GET /api/v1/meta`
- `GET /api/v1/sources`
- `GET /api/v1/sources/{source_id}/layers`

### Environmental data

- `GET /api/v1/weather?lat=...&lon=...`
- `GET /api/v1/features/probe?lat=...&lon=...&include_wms=true`

### Forecast map

`GET /api/v1/cells?...&data_mode=demo|live|store`

- **demo**: deterministic synthetic habitat for development only.
- **live**: real Kartverket terrain/elevation per H3 cell, bounded by a strict request limit.
- **store**: pre-ingested PostGIS H3 features; missing rows are visibly flagged and fall back to demo data.

## Run locally

```bash
cp .env.example .env
docker compose up --build
```

UI: `http://localhost:5173`

OpenAPI: `http://localhost:8000/docs`

## Build a real H3 feature snapshot

```bash
python scripts/ingest_live_features.py \
  --lat 58.735 --lon 5.647 --radius-km 1 \
  --resolution 9 --out data/jaren.jsonl
```

Fast terrain-only extraction:

```bash
python scripts/ingest_live_features.py \
  --lat 58.735 --lon 5.647 --radius-km 1 \
  --resolution 9 --fast --out data/jaren-fast.jsonl
```

Load into PostGIS:

```bash
python scripts/load_feature_store.py data/jaren.jsonl
```

Then request the same area with `data_mode=store`.

## Occurrence extraction

The Artskart API exposes many filters. Keep the exact query used by each model run so training data is reproducible:

```bash
python scripts/artskart_export.py \
  --param 'countys[]=11' \
  --out data/artskart-rogaland.json
```

For national model training, prefer a reproducible bulk pipeline and retain source metadata/license/citation information with each snapshot.

## Scientific rules

- Suitability is **not** confirmed presence.
- Forecast scores are **not** species identification or edibility advice.
- Synthetic fallback cells are explicitly labelled.
- Raw upstream evidence is retained separately from derived features.
- Spatial validation is required; random row splits alone are not accepted for SDM evaluation.
- Model version, feature version and source lineage belong with every production prediction.

See `docs/ARCHITECTURE.md`, `docs/DATA_PIPELINE.md`, `docs/DATA_SOURCES.md` and `docs/ROADMAP.md`.
