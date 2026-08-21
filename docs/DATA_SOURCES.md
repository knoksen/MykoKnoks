# Norwegian & Nordic data-source plan

## Artsdatabanken — Artskart

Purpose: georeferenced species occurrences for training and validation.

- Public API: `https://artskart.artsdatabanken.no/publicapi/`
- Observations: `/api/Observations/list/`
- Taxonomy: `/api/taxon`
- Preserve source record ID, dataset ID, coordinate uncertainty and raw provenance.

## MET Norway

Purpose: current/forecast fruiting conditions and later historical feature engineering.

- `https://api.met.no/weatherapi/locationforecast/2.0/compact`
- Requires a unique identifying `User-Agent`.
- Nordic short-range forecasts use MEPS; MET documents 2.5 km horizontal resolution for 0–60 hours.

Candidate lag features: temperature 3/7/14/21 d, precipitation 3/7/14/21/30 d, humidity duration, dry-spell length and temperature × moisture interactions.

## NIBIO SR16

Purpose: forest structure, dominant tree species and forest context.

WMS: `https://wms.nibio.no/cgi-bin/sr16?VERSION=1.3.0&SERVICE=WMS&REQUEST=GetCapabilities`

The 2026 product includes raster/vector products and properties such as tree species, volume, mean height, biomass and site index.

## NIBIO AR5

Purpose: fine-scale land-resource classes, especially grassland, cultivated land, forest and open land. Use official NIBIO/Geonorge services and persist dataset versions.

## Kartverket — National Detailed Height Model

Purpose: elevation, slope, aspect and wetness/topographic-position proxies. Kartverket documents national 1 m terrain data plus 1/10/50 m terrain-model products and API/download access.

## NGU — loose sediments / geology

Purpose: substrate and drainage correlates.

WMS: `https://geo.ngu.no/mapserver/LosmasserWMS2`

## Copernicus Sentinel-2

Purpose: vegetation condition, phenology and moisture proxies.

Current CDSE STAC endpoint: `https://stac.dataspace.copernicus.eu/v1/`

Use Sentinel-2 Level-2A with cloud masking and derived vegetation/moisture indices. Do not use the legacy STAC endpoint deprecated in 2025.

## Storage

Raw JSON/NDJSON + provenance; COG for rasters; Parquet/GeoParquet for analytical tables; PostGIS for serving/querying; PMTiles for map delivery; H3 as spatial key.
