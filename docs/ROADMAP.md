# Roadmap

## Phase 0 — included
- [x] FastAPI service
- [x] MapLibre React UI
- [x] H3 prediction grid
- [x] MET Norway live-weather adapter
- [x] Artskart adapter scaffold
- [x] Copernicus STAC adapter scaffold
- [x] PostGIS schema
- [x] baseline ML code
- [x] Docker/CI/tests

## Phase 1 — Norway production data
- [ ] Artskart incremental ingestion + QA/taxonomy/uncertainty
- [ ] NIBIO AR5 H3 fractions
- [ ] NIBIO SR16 forest/tree features
- [ ] Kartverket DTM terrain features
- [ ] NGU substrate features
- [ ] historical weather feature store
- [ ] Sentinel-2 cloud-masked seasonal composites

## Phase 2 — species distribution models
- [ ] background/pseudo-absence strategy
- [ ] spatial block cross-validation
- [ ] gradient boosting baseline per species
- [ ] probability calibration + uncertainty surfaces
- [ ] model cards and lineage

## Phase 3 — temporal fruiting
- [ ] lagged weather engineering
- [ ] seasonality vs immediate trigger separation
- [ ] evaluate 1/3/7/10-day forecast skill
- [ ] weather ensemble uncertainty

## Phase 4 — productisation
- [ ] accounts + private observations
- [ ] exact-location privacy controls
- [ ] offline regions / PMTiles
- [ ] Android wrapper if needed beyond PWA
- [ ] Norwegian + English UI
- [ ] explainability panel and alerts

## Phase 5 — Nordic biodiversity engine
- [ ] Sweden/Finland/Denmark adapters
- [ ] broader fungi modules
- [ ] plants/invasive species/forest-health modules
- [ ] ecology digital-twin API for GIS/BIM/land-management integration
