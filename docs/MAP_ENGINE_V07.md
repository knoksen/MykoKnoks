# MykoKnoks v0.7 Map Engine

The v0.7 map upgrade replaces the MapLibre demo basemap with official Kartverket WMTS raster basemaps and adds a more GIS-oriented interaction layer.

## Basemaps

- `topo` — Kartverket topographic colour map
- `topograatone` — Kartverket greyscale topographic map
- `toporaster` — Kartverket topographic raster map

All three use the public Web Mercator WMTS tile endpoint under `https://cache.kartverket.no/v1/wmts/1.0.0/`.

## Interaction

- persistent basemap preference
- fit-to-results control
- geolocation, fullscreen, navigation and metric scale controls
- cursor coordinate readout
- hover cell outline and metric preview
- selected-cell emphasis
- search-centre marker
- separate H3 line layer with zoom-aware width
- automatic result fitting after a forecast run

## Scientific display

H3 forecast cells remain clearly separate from the basemap. The map visualises the selected model metric and does not imply observed species presence.

## Satellite imagery

Norge i bilder WMTS requires a token. v0.7 deliberately does not hard-code credentials or use an unauthenticated workaround. A future configuration panel can add a user/server-provided token without exposing it in the repository.
