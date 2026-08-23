# MykoKnoks v0.8 — Ecological GIS

MykoKnoks v0.8 extends the v0.7 Kartverket map engine into a multi-provider ecological GIS workspace.

## Open WMS overlays

The layer tree uses public mapping services directly and does not embed private credentials:

- **NIBIO AR5 Arealtype** — detailed land-resource classes.
- **NIBIO SR16 Treslag** — dominant forest tree species.
- **NIBIO SR16 Skoghøyde** — forest structural height context.
- **NGU Løsmasser** — superficial geology / Quaternary deposits.
- **Kartverket DTM Skyggerelieff** — hillshade from the national elevation service.
- **Kartverket DTM Helning** — terrain slope in degrees.
- **Miljødirektoratet Hovedøkosystemer** — ecosystem classes including wetland.
- **Artsdatabanken Artskart** — red-listed species WMS publication.

Every open overlay has an independent visibility toggle and opacity control. Where the provider exposes `GetLegendGraphic`, MykoKnoks can show the provider legend.

## Click-to-inspect

When one or more queryable WMS overlays are active, clicking the map sends `GetFeatureInfo` requests for those layers. In Electron, requests use the existing main-process HTTP bridge to avoid renderer CORS limitations. The returned provider text is shown in the Inspect panel without pretending that raster WMS pixels are locally authoritative vector features.

H3 selection still works on the same click, so ecological context and MykoKnoks model-cell inspection can be used together.

## Norge i bilder

Norge i bilder is represented in the layer tree but intentionally locked in the repository build. As of the 2026 service transition, WMS/WMTS access requires a time-limited token tied to an authorised GeoID/Norge digitalt user or agreement. MykoKnoks links to the official token page but does not request, store or commit credentials.

A later credential adapter can accept a user-supplied session token locally and resolve the authorised WMS/WMTS layer catalogue without placing the token in Git or application logs.

## Scientific boundary

These overlays provide ecological and geographic context. Displaying an AR5, SR16, geology, wetland or occurrence layer does not convert the current MykoKnoks heuristic suitability score into a validated species-distribution probability. The source layers should eventually become explicit model features with provenance, versioning and spatial cross-validation before they are treated as predictive evidence.
