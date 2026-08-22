# MykoKnoks v0.4 UI/UX

This release turns the functional desktop client into a map-first ecological intelligence workspace.

## Product goals

- Reduce visual hierarchy noise and keep the map as the primary work surface.
- Wire map-cell selection into a persistent inspector instead of transient popups.
- Expose the four score dimensions (combined, habitat, fruiting, confidence) as first-class map layers.
- Make Demo, Live and H3 Store modes explicit and understandable.
- Surface provenance, drivers and scientific warnings next to the selected cell.
- Keep API state, desktop export actions and runtime information visible without consuming map space.
- Preserve Android and web compatibility while enhancing the Electron desktop shell.

## Interaction model

1. Configure species, location, radius, resolution and data mode in the left rail.
2. Run a forecast.
3. Switch score layer directly over the map.
4. Click an H3 cell to inspect score decomposition, environmental context, drivers and provenance.
5. Use Sources/System tabs for backend and data-pipeline diagnostics.
6. Export screenshots/PDF from the desktop top bar.

## Scientific semantics

The UI deliberately says suitability rather than confirmed presence. Demo remains synthetic. Real-data cells display confidence and provenance. v0.4 does not relabel heuristic scores as validated occurrence probabilities.
