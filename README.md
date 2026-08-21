# MykoKnoks

**Nordic fungal habitat & fruiting forecast engine** — an open, auditable geospatial MVP for Norway first, Nordic expansion next.

MykoKnoks separates two questions:

1. **WHERE?** Habitat suitability from terrain, soil, land cover, forest/tree and occurrence data.
2. **WHEN?** Fruiting potential from recent and forecast weather.

The app combines both into a transparent score instead of pretending a map cell guarantees a mushroom is present.

## MVP architecture

```text
Artskart / CSV occurrences        MET Norway weather
          |                              |
          v                              v
   occurrence features            weather features
          |                              |
          +------------+-----------------+
                       v
              scoring / ML layer
                       |
                 H3 spatial grid
                       |
             FastAPI + PostGIS
                       |
           MapLibre React PWA
```

## Included now

- FastAPI backend with health, metadata, weather and H3 forecast-cell endpoints.
- MET Norway `Locationforecast/2.0/compact` client with mandatory identifying User-Agent.
- Artsdatabanken/Artskart adapter scaffold.
- H3 resolution 9 map cells (~0.1 km² average cell area).
- Explainable habitat + fruiting score model and confidence field.
- React + TypeScript + MapLibre map UI.
- Installable PWA baseline for desktop/Android browser installation.
- PostgreSQL/PostGIS schema for observations, environmental features, weather and predictions.
- Baseline ML training script using scikit-learn HistGradientBoostingClassifier.
- Docker Compose local stack.
- CI workflow and Python tests.
- Data-source and architecture documentation.

## Quick start

### Docker

```bash
cp .env.example .env
docker compose up --build
```

Open UI at `http://localhost:5173` and API docs at `http://localhost:8000/docs`.

## Scoring model

```text
combined_score = habitat_score × fruiting_score
```

The v0.1 habitat layer is deterministic synthetic demo data so the complete stack runs before production raster ingestion. It must not be interpreted as real habitat measurements.

Production data targets: Artskart, NIBIO SR16/AR5, Kartverket DTM, NGU geology/loose sediments, Copernicus Sentinel-2 and MET Norway.

## Safety

MykoKnoks predicts environmental suitability, not confirmed presence or edibility. Never use forecast scores as species identification.

See `docs/ARCHITECTURE.md`, `docs/DATA_SOURCES.md` and `docs/ROADMAP.md`.
