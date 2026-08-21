# Data sources

MykoKnoks uses a source-registry approach. Endpoints are configurable through environment variables so upstream service changes do not require rewriting scoring logic.

## Artsdatabanken

- Artskart public API for observations and taxonomy.
- Artsobservasjoner / Darwin Core bulk datasets are preferred for large reproducible training snapshots.
- Observation data must retain source ids, dates, coordinate uncertainty and dataset attribution.

## MET Norway

- Locationforecast 2.0 for operational weather forecasts.
- MykoKnoks supplies an identifying User-Agent as required by MET Norway.
- Historical/lagged weather requires a dedicated ingestion strategy and is not yet claimed as complete in v0.2.

## Kartverket / Geonorge

- Elevation WPS is used for point-level real terrain/elevation evidence.
- Production terrain derivatives should be generated from downloaded DTM coverage rather than issuing a point request for every national H3 cell.

## NIBIO

- AR5: land-resource / land-cover evidence.
- SR16: forest-resource evidence.
- v0.2 discovers WMS layers dynamically and can issue point feature-info probes.
- Production H3 features should be built from bulk vector/raster data to obtain area fractions and robust statistics.

## NGU

- Løsmasser WMS provides Quaternary-geology evidence.
- NGU attribution and NLOD requirements must be retained with derived products.
- Prefer OGC API Features / bulk vector access for production normalization when practical.

## Copernicus

- Sentinel-2 L2A discovery via Copernicus Data Space STAC.
- Production vegetation features require cloud masking, seasonal composites and a documented index pipeline.

## Provenance fields

At minimum retain:

- source id
- source dataset/layer
- acquisition time
- feature version
- raw payload or immutable raw-file reference
- license/attribution metadata
- normalization code/model version
- quality/completeness indicators
