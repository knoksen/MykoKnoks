# Roadmap

## Phase 0 — foundation ✅

- [x] FastAPI service
- [x] MapLibre React UI
- [x] H3 prediction grid
- [x] MET Norway live-weather adapter
- [x] Artskart adapter scaffold
- [x] Copernicus STAC adapter scaffold
- [x] PostGIS schema
- [x] baseline ML training code
- [x] Docker/CI/test baseline
- [x] provenance-first data-source architecture

## Phase 1 — Norway production data 🟡

- [x] Kartverket elevation/terrain WPS client
- [x] NIBIO AR5 WMS discovery + live feature-info adapter
- [x] NIBIO SR16 WMS discovery + live feature-info adapter
- [x] NGU Løsmasser WMS discovery + live feature-info adapter
- [x] controlled H3 ingestion CLI
- [x] PostGIS normalized feature-store loader
- [x] raw H3 evidence/provenance table
- [x] live/store/demo API modes with explicit fallback flags
- [ ] Artskart pagination + incremental checkpoints + raw archive manifest
- [ ] occurrence QA: duplicate, uncertainty, date and taxonomy validation
- [ ] AR5 polygon-to-H3 fractions rather than point-only evidence
- [ ] SR16 raster/vector aggregation per H3 cell
- [ ] DTM-derived slope/aspect/TWI at production scale
- [ ] NGU substrate normalization dictionary
- [ ] historical weather feature store (ERA5/MET strategy)
- [ ] Sentinel-2 cloud-masked seasonal composites and NDVI/EVI

## Phase 2 — species distribution models

- [ ] target-species taxonomy resolver
- [ ] background/pseudo-absence sampling strategy
- [x] grouped spatial train/test baseline
- [ ] multi-fold spatial block cross-validation
- [ ] gradient boosting baseline per species
- [ ] calibration: reliability curves + Brier score
- [ ] uncertainty surfaces
- [ ] model cards with source/version lineage

## Phase 3 — temporal fruiting model

- [ ] lagged temperature / rainfall / humidity features
- [ ] growing degree-day and accumulated precipitation features
- [ ] separate seasonal prior from short-term fruiting trigger
- [ ] 1/3/7/10-day forecast-skill evaluation
- [ ] weather ensemble uncertainty

## Phase 4 — productisation

- [ ] account/auth layer
- [ ] private user observations
- [ ] public contribution flow
- [ ] exact-location privacy and rare-species obfuscation
- [ ] offline map region download
- [x] PWA baseline
- [ ] optional Capacitor Android wrapper
- [ ] PMTiles national prediction layers
- [ ] Norwegian/English UI
- [ ] explainability panel / driver charts
- [ ] alerts for chosen species/areas

## Phase 5 — Nordic biodiversity engine

- [ ] Sweden, Finland and Denmark source adapters
- [ ] fungi beyond initial species set
- [ ] plants and invasive-species modules
- [ ] forest-health and habitat-restoration modules
- [ ] ecological digital-twin API for GIS/BIM/land-management systems
- [ ] scenario engine for climate and land-use change
