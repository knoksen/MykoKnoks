import { useEffect, useMemo, useRef, useState } from 'react'
import maplibregl, { Map as MapLibreMap } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { ForecastCollection, ForecastFeature } from '../api'
import {
  GIS_GROUP_LABELS,
  GIS_LAYERS,
  identifyWmsLayer,
  initialGISState,
  type GISIdentifyResult,
  type GISLayerDefinition,
  type GISLayerGroup,
  type GISLayerRuntimeState,
  wmsLegendUrl,
  wmsTileUrl,
} from '../gisLayers'

export type MapMetric = 'combined' | 'habitat' | 'fruiting' | 'confidence'
type BasemapId = 'topo' | 'gray' | 'terrain'

type Props = {
  data: ForecastCollection | null
  center: [number, number]
  metric: MapMetric
  selectedH3?: string | null
  minScore?: number
  fillOpacity?: number
  showOutlines?: boolean
  onSelect?: (feature: ForecastFeature | null) => void
}

type HoverInfo = {
  h3: string
  value: number
  synthetic: boolean
}

type InspectPoint = {
  lng: number
  lat: number
}

const SOURCE = 'forecast-cells'
const CENTER_SOURCE = 'search-center'
const FILL_LAYER = 'forecast-fill'
const LINE_LAYER = 'forecast-lines'
const HOVER_LAYER = 'forecast-hover'
const SELECTED_LAYER = 'forecast-selected'
const CENTER_LAYER = 'search-center-point'
const BASEMAP_STORAGE = 'mykoknoks.v07.basemap'
const GIS_STORAGE = 'mykoknoks.v08.gis-layers'

const BASEMAPS: Record<BasemapId, { label: string; short: string; layer: string }> = {
  topo: { label: 'Topo', short: 'COLOR', layer: 'topo' },
  gray: { label: 'Gray', short: 'CLEAN', layer: 'topograatone' },
  terrain: { label: 'Raster', short: 'TERRAIN', layer: 'toporaster' },
}

const METRIC_LABELS: Record<MapMetric, string> = {
  combined: 'Suitability',
  habitat: 'Habitat',
  fruiting: 'Fruiting',
  confidence: 'Confidence',
}

function clamp01(value: number) {
  return Math.max(0, Math.min(1, value))
}

function readBasemap(): BasemapId {
  try {
    const value = window.localStorage.getItem(BASEMAP_STORAGE)
    if (value === 'topo' || value === 'gray' || value === 'terrain') return value
  } catch {
    // Storage is optional.
  }
  return 'topo'
}

function readGISState(): Record<string, GISLayerRuntimeState> {
  const fallback = initialGISState()
  try {
    const raw = window.localStorage.getItem(GIS_STORAGE)
    if (!raw) return fallback
    const parsed = JSON.parse(raw) as Record<string, Partial<GISLayerRuntimeState>>
    for (const layer of GIS_LAYERS) {
      const saved = parsed[layer.id]
      if (!saved) continue
      fallback[layer.id] = {
        visible: layer.restricted ? false : Boolean(saved.visible),
        opacity: typeof saved.opacity === 'number' ? clamp01(saved.opacity) : layer.defaultOpacity,
      }
    }
  } catch {
    // Invalid local state should never break the map.
  }
  return fallback
}

function tileUrl(layer: string) {
  return `https://cache.kartverket.no/v1/wmts/1.0.0/${layer}/default/webmercator/{z}/{y}/{x}.png`
}

function basemapStyle(id: BasemapId) {
  const layer = BASEMAPS[id].layer
  return {
    version: 8,
    sources: {
      'kartverket-basemap': {
        type: 'raster',
        tiles: [tileUrl(layer)],
        tileSize: 256,
        minzoom: 0,
        maxzoom: 20,
        attribution: '© Kartverket',
      },
    },
    layers: [
      {
        id: 'background',
        type: 'background',
        paint: { 'background-color': '#08110d' },
      },
      {
        id: 'kartverket-basemap',
        type: 'raster',
        source: 'kartverket-basemap',
        minzoom: 0,
        maxzoom: 20,
        paint: {
          'raster-opacity': 1,
          'raster-fade-duration': 180,
          'raster-saturation': id === 'gray' ? -0.15 : 0,
          'raster-contrast': id === 'terrain' ? 0.08 : 0.02,
        },
      },
    ],
  } as any
}

function metricExpression(metric: MapMetric) {
  return [
    'interpolate', ['linear'], ['coalesce', ['get', metric], 0],
    0, '#16231d',
    0.18, '#465236',
    0.38, '#83743a',
    0.58, '#a0ad4a',
    0.78, '#56d277',
    1, '#2df58a',
  ] as any
}

function scoreFilter(metric: MapMetric, minScore: number) {
  return ['>=', ['coalesce', ['get', metric], 0], clamp01(minScore)] as any
}

function opacityExpression(fillOpacity: number) {
  const opacity = Math.max(0.08, Math.min(1, fillOpacity))
  return ['case', ['get', 'synthetic_habitat'], opacity * 0.58, opacity * 0.82] as any
}

function emptyCollection() {
  return { type: 'FeatureCollection', features: [] } as any
}

function pointCollection(center: [number, number]) {
  return {
    type: 'FeatureCollection',
    features: [{
      type: 'Feature',
      geometry: { type: 'Point', coordinates: center },
      properties: {},
    }],
  } as any
}

function extendCoordinates(bounds: maplibregl.LngLatBounds, coordinates: unknown) {
  if (!Array.isArray(coordinates)) return
  if (
    coordinates.length >= 2
    && typeof coordinates[0] === 'number'
    && typeof coordinates[1] === 'number'
  ) {
    bounds.extend([coordinates[0], coordinates[1]])
    return
  }
  for (const child of coordinates) extendCoordinates(bounds, child)
}

function fitToCollection(map: MapLibreMap, data: ForecastCollection | null) {
  if (!data?.features.length) return
  const bounds = new maplibregl.LngLatBounds()
  for (const feature of data.features) {
    extendCoordinates(bounds, (feature.geometry as any)?.coordinates)
  }
  if (bounds.isEmpty()) return
  map.fitBounds(bounds, {
    padding: { top: 74, right: 70, bottom: 78, left: 70 },
    maxZoom: 13.2,
    duration: 650,
  })
}

function overlaySourceId(id: string) {
  return `eco-source-${id}`
}

function overlayLayerId(id: string) {
  return `eco-layer-${id}`
}

function cleanFeatureInfo(body: string) {
  return body
    .replace(/<[^>]+>/g, ' ')
    .replace(/\r/g, '')
    .replace(/[ \t]+/g, ' ')
    .replace(/\n\s*\n+/g, '\n')
    .trim()
}

export default function MapView({
  data,
  center,
  metric,
  selectedH3,
  minScore = 0,
  fillOpacity = 0.76,
  showOutlines = true,
  onSelect,
}: Props) {
  const container = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<MapLibreMap | null>(null)
  const dataRef = useRef<ForecastCollection | null>(data)
  const selectRef = useRef(onSelect)
  const metricRef = useRef(metric)
  const minScoreRef = useRef(minScore)
  const opacityRef = useRef(fillOpacity)
  const outlinesRef = useRef(showOutlines)
  const selectedRef = useRef(selectedH3 || '')
  const centerRef = useRef(center)
  const appliedBasemap = useRef<BasemapId | null>(null)

  const [basemap, setBasemap] = useState<BasemapId>(() => readBasemap())
  const [hover, setHover] = useState<HoverInfo | null>(null)
  const [cursor, setCursor] = useState<[number, number] | null>(null)
  const [layersOpen, setLayersOpen] = useState(true)
  const [gisState, setGISState] = useState<Record<string, GISLayerRuntimeState>>(() => readGISState())
  const gisStateRef = useRef(gisState)
  const [legendId, setLegendId] = useState<string | null>(null)
  const [inspectPoint, setInspectPoint] = useState<InspectPoint | null>(null)
  const [inspection, setInspection] = useState<GISIdentifyResult[]>([])
  const [inspectionLoading, setInspectionLoading] = useState(false)

  dataRef.current = data
  selectRef.current = onSelect
  metricRef.current = metric
  minScoreRef.current = minScore
  opacityRef.current = fillOpacity
  outlinesRef.current = showOutlines
  selectedRef.current = selectedH3 || ''
  centerRef.current = center
  gisStateRef.current = gisState

  const activeLayers = useMemo(
    () => GIS_LAYERS.filter(layer => !layer.restricted && gisState[layer.id]?.visible),
    [gisState],
  )

  const groupedLayers = useMemo(() => {
    const groups = new Map<GISLayerGroup, GISLayerDefinition[]>()
    for (const layer of GIS_LAYERS) {
      const list = groups.get(layer.group) || []
      list.push(layer)
      groups.set(layer.group, list)
    }
    return [...groups.entries()]
  }, [])

  function syncRasterOverlays(map: MapLibreMap) {
    for (const definition of GIS_LAYERS) {
      const sourceId = overlaySourceId(definition.id)
      const layerId = overlayLayerId(definition.id)
      const state = gisStateRef.current[definition.id]
      const visible = Boolean(state?.visible) && !definition.restricted
      const tile = wmsTileUrl(definition)

      if (!visible || !tile) {
        if (map.getLayer(layerId)) map.removeLayer(layerId)
        if (map.getSource(sourceId)) map.removeSource(sourceId)
        continue
      }

      if (!map.getSource(sourceId)) {
        map.addSource(sourceId, {
          type: 'raster',
          tiles: [tile],
          tileSize: 256,
          minzoom: definition.minZoom ?? 0,
          maxzoom: definition.maxZoom ?? 20,
          attribution: `© ${definition.provider}`,
        })
      }

      if (!map.getLayer(layerId)) {
        const before = map.getLayer(FILL_LAYER) ? FILL_LAYER : undefined
        map.addLayer({
          id: layerId,
          type: 'raster',
          source: sourceId,
          minzoom: definition.minZoom ?? 0,
          maxzoom: definition.maxZoom ?? 20,
          paint: {
            'raster-opacity': clamp01(state?.opacity ?? definition.defaultOpacity),
            'raster-fade-duration': 100,
          },
        }, before)
      } else {
        map.setPaintProperty(layerId, 'raster-opacity', clamp01(state?.opacity ?? definition.defaultOpacity))
      }
    }
  }

  function installAnalysisLayers(map: MapLibreMap) {
    syncRasterOverlays(map)

    if (!map.getSource(SOURCE)) {
      map.addSource(SOURCE, {
        type: 'geojson',
        data: dataRef.current || emptyCollection(),
      })
    }

    if (!map.getSource(CENTER_SOURCE)) {
      map.addSource(CENTER_SOURCE, {
        type: 'geojson',
        data: pointCollection(centerRef.current),
      })
    }

    if (!map.getLayer(FILL_LAYER)) {
      map.addLayer({
        id: FILL_LAYER,
        type: 'fill',
        source: SOURCE,
        filter: scoreFilter(metricRef.current, minScoreRef.current),
        paint: {
          'fill-color': metricExpression(metricRef.current),
          'fill-opacity': opacityExpression(opacityRef.current),
        },
      })
    }

    if (!map.getLayer(LINE_LAYER)) {
      map.addLayer({
        id: LINE_LAYER,
        type: 'line',
        source: SOURCE,
        filter: scoreFilter(metricRef.current, minScoreRef.current),
        paint: {
          'line-color': 'rgba(224,255,236,.72)',
          'line-opacity': outlinesRef.current ? 0.58 : 0,
          'line-width': ['interpolate', ['linear'], ['zoom'], 7, 0.35, 10, 0.75, 13, 1.25] as any,
        },
      })
    }

    if (!map.getLayer(HOVER_LAYER)) {
      map.addLayer({
        id: HOVER_LAYER,
        type: 'line',
        source: SOURCE,
        filter: ['==', ['get', 'h3'], ''] as any,
        paint: {
          'line-color': '#69f39d',
          'line-width': 2.5,
          'line-opacity': 0.96,
          'line-blur': 0.15,
        },
      })
    }

    if (!map.getLayer(SELECTED_LAYER)) {
      map.addLayer({
        id: SELECTED_LAYER,
        type: 'line',
        source: SOURCE,
        filter: ['==', ['get', 'h3'], selectedRef.current] as any,
        paint: {
          'line-color': '#ffffff',
          'line-width': 3.5,
          'line-opacity': 0.98,
        },
      })
    }

    if (!map.getLayer(CENTER_LAYER)) {
      map.addLayer({
        id: CENTER_LAYER,
        type: 'circle',
        source: CENTER_SOURCE,
        paint: {
          'circle-radius': 4.5,
          'circle-color': '#07110b',
          'circle-stroke-color': '#baffd0',
          'circle-stroke-width': 2,
          'circle-opacity': 0.9,
        },
      })
    }
  }

  async function inspectAt(map: MapLibreMap, event: maplibregl.MapMouseEvent) {
    const queryable = GIS_LAYERS.filter(layer => {
      const state = gisStateRef.current[layer.id]
      return !layer.restricted && layer.queryable && state?.visible
    })

    setInspectPoint({ lng: event.lngLat.lng, lat: event.lngLat.lat })
    if (!queryable.length) {
      setInspection([])
      return
    }

    const bounds = map.getBounds()
    const canvas = map.getCanvas()
    setInspectionLoading(true)
    try {
      const results = await Promise.all(queryable.map(layer => identifyWmsLayer(layer, {
        lng: event.lngLat.lng,
        lat: event.lngLat.lat,
        west: bounds.getWest(),
        south: bounds.getSouth(),
        east: bounds.getEast(),
        north: bounds.getNorth(),
        width: canvas.clientWidth,
        height: canvas.clientHeight,
        x: event.point.x,
        y: event.point.y,
      })))
      setInspection(results.map(result => ({ ...result, body: cleanFeatureInfo(result.body) })))
    } finally {
      setInspectionLoading(false)
    }
  }

  function openExternal(url: string) {
    if (window.mykoDesktop?.openExternal) {
      void window.mykoDesktop.openExternal(url)
      return
    }
    window.open(url, '_blank', 'noopener,noreferrer')
  }

  useEffect(() => {
    if (!container.current || mapRef.current) return

    const map = new maplibregl.Map({
      container: container.current,
      style: basemapStyle(basemap),
      center,
      zoom: 9.8,
      pitch: 0,
      bearing: 0,
      attributionControl: false,
      maxZoom: 20,
    })
    appliedBasemap.current = basemap

    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right')
    map.addControl(new maplibregl.GeolocateControl({
      positionOptions: { enableHighAccuracy: true },
      trackUserLocation: true,
    }), 'top-right')
    map.addControl(new maplibregl.FullscreenControl(), 'top-right')
    map.addControl(new maplibregl.ScaleControl({ maxWidth: 130, unit: 'metric' }), 'bottom-right')
    map.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right')

    map.on('style.load', () => {
      installAnalysisLayers(map)
      map.resize()
    })

    map.on('mouseenter', FILL_LAYER, () => {
      map.getCanvas().style.cursor = 'pointer'
    })

    map.on('mousemove', event => {
      setCursor([event.lngLat.lng, event.lngLat.lat])
    })

    map.on('mousemove', FILL_LAYER, event => {
      const properties = event.features?.[0]?.properties as Record<string, unknown> | undefined
      const h3 = String(properties?.h3 || '')
      if (!h3) return
      const value = Number(properties?.[metricRef.current] || 0)
      setHover({
        h3,
        value,
        synthetic: Boolean(properties?.synthetic_habitat),
      })
      if (map.getLayer(HOVER_LAYER)) {
        map.setFilter(HOVER_LAYER, ['==', ['get', 'h3'], h3] as any)
      }
    })

    map.on('mouseleave', FILL_LAYER, () => {
      map.getCanvas().style.cursor = ''
      setHover(null)
      if (map.getLayer(HOVER_LAYER)) {
        map.setFilter(HOVER_LAYER, ['==', ['get', 'h3'], ''] as any)
      }
    })

    map.on('click', event => {
      const hits = map.getLayer(FILL_LAYER)
        ? map.queryRenderedFeatures(event.point, { layers: [FILL_LAYER] })
        : []
      const h3 = String(hits[0]?.properties?.h3 || '')
      const feature = h3
        ? dataRef.current?.features.find(item => item.properties.h3 === h3) || null
        : null
      selectRef.current?.(feature)
      void inspectAt(map, event)
    })

    mapRef.current = map
    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

  useEffect(() => {
    const map = mapRef.current
    if (!map || appliedBasemap.current === basemap) return
    appliedBasemap.current = basemap
    try { window.localStorage.setItem(BASEMAP_STORAGE, basemap) } catch { /* optional preference */ }
    setHover(null)
    map.setStyle(basemapStyle(basemap), { diff: false })
  }, [basemap])

  useEffect(() => {
    try { window.localStorage.setItem(GIS_STORAGE, JSON.stringify(gisState)) } catch { /* optional */ }
    gisStateRef.current = gisState
    const map = mapRef.current
    if (!map) return
    const update = () => syncRasterOverlays(map)
    if (map.isStyleLoaded()) update()
    else map.once('style.load', update)
  }, [gisState])

  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const update = () => {
      installAnalysisLayers(map)
      const source = map.getSource(SOURCE) as maplibregl.GeoJSONSource | undefined
      source?.setData(data || emptyCollection())
      if (data?.features.length) fitToCollection(map, data)
      else map.easeTo({ center, duration: 450 })
    }
    if (map.isStyleLoaded()) update()
    else map.once('style.load', update)
  }, [data])

  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const update = () => {
      installAnalysisLayers(map)
      const source = map.getSource(CENTER_SOURCE) as maplibregl.GeoJSONSource | undefined
      source?.setData(pointCollection(center))
      if (!dataRef.current?.features.length) map.easeTo({ center, duration: 400 })
    }
    if (map.isStyleLoaded()) update()
    else map.once('style.load', update)
  }, [center])

  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const update = () => {
      if (!map.getLayer(FILL_LAYER) || !map.getLayer(LINE_LAYER)) return
      const filter = scoreFilter(metric, minScore)
      map.setPaintProperty(FILL_LAYER, 'fill-color', metricExpression(metric))
      map.setFilter(FILL_LAYER, filter)
      map.setFilter(LINE_LAYER, filter)
    }
    if (map.isStyleLoaded()) update()
    else map.once('style.load', update)
  }, [metric, minScore])

  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const update = () => {
      if (map.getLayer(FILL_LAYER)) {
        map.setPaintProperty(FILL_LAYER, 'fill-opacity', opacityExpression(fillOpacity))
      }
      if (map.getLayer(LINE_LAYER)) {
        map.setPaintProperty(LINE_LAYER, 'line-opacity', showOutlines ? 0.58 : 0)
      }
    }
    if (map.isStyleLoaded()) update()
    else map.once('style.load', update)
  }, [fillOpacity, showOutlines])

  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const update = () => {
      if (map.getLayer(SELECTED_LAYER)) {
        map.setFilter(SELECTED_LAYER, ['==', ['get', 'h3'], selectedH3 || ''] as any)
      }
    }
    if (map.isStyleLoaded()) update()
    else map.once('style.load', update)
  }, [selectedH3])

  return (
    <div className="map-pro-shell eco-gis-shell">
      <div ref={container} className="map" />

      <div className="basemap-switcher" role="group" aria-label="Basemap">
        {(Object.keys(BASEMAPS) as BasemapId[]).map(id => (
          <button
            type="button"
            key={id}
            className={basemap === id ? 'active' : ''}
            onClick={() => setBasemap(id)}
            title={`Kartverket ${BASEMAPS[id].label}`}
          >
            <strong>{BASEMAPS[id].label}</strong>
            <small>{BASEMAPS[id].short}</small>
          </button>
        ))}
      </div>

      <button
        type="button"
        className={`eco-layer-toggle ${layersOpen ? 'active' : ''}`}
        onClick={() => setLayersOpen(value => !value)}
        title="Ecological GIS layer tree"
      >
        Layers <b>{activeLayers.length}</b>
      </button>

      {layersOpen && (
        <aside className="eco-layer-tree" aria-label="Ecological GIS layers">
          <header>
            <div>
              <strong>Ecological GIS</strong>
              <span>WMS overlays · click map to inspect</span>
            </div>
            <button type="button" onClick={() => setLayersOpen(false)}>×</button>
          </header>

          <div className="eco-layer-scroll">
            {groupedLayers.map(([group, layers]) => (
              <section className="eco-layer-group" key={group}>
                <h4>{GIS_GROUP_LABELS[group]}</h4>
                {layers.map(layer => {
                  const state = gisState[layer.id] || { visible: false, opacity: layer.defaultOpacity }
                  const legend = wmsLegendUrl(layer)
                  return (
                    <div className={`eco-layer-item ${state.visible ? 'enabled' : ''} ${layer.restricted ? 'restricted' : ''}`} key={layer.id}>
                      <div className="eco-layer-main">
                        <label>
                          <input
                            type="checkbox"
                            checked={state.visible}
                            disabled={layer.restricted}
                            onChange={event => setGISState(current => ({
                              ...current,
                              [layer.id]: { ...state, visible: event.target.checked },
                            }))}
                          />
                          <span className="eco-layer-check" />
                          <span className="eco-layer-name">
                            <strong>{layer.label}</strong>
                            <small>{layer.provider} · {layer.short}</small>
                          </span>
                        </label>
                        {layer.restricted && <em>LOCKED</em>}
                      </div>

                      <p>{layer.description}</p>

                      {!layer.restricted && (
                        <div className="eco-layer-controls">
                          <span>{Math.round(state.opacity * 100)}%</span>
                          <input
                            type="range"
                            min="10"
                            max="100"
                            step="5"
                            value={Math.round(state.opacity * 100)}
                            aria-label={`${layer.label} opacity`}
                            onChange={event => setGISState(current => ({
                              ...current,
                              [layer.id]: { ...state, opacity: Number(event.target.value) / 100 },
                            }))}
                          />
                          {legend && (
                            <button type="button" onClick={() => setLegendId(current => current === layer.id ? null : layer.id)}>
                              Legend
                            </button>
                          )}
                          <button type="button" onClick={() => openExternal(layer.sourceUrl)}>Source</button>
                        </div>
                      )}

                      {layer.restricted && (
                        <div className="eco-restricted-note">
                          Requires time-limited GeoID/Norge digitalt token. Credentials are never stored in the repository.
                          <button type="button" onClick={() => openExternal('https://services.norgeibilder.no/token')}>Get token</button>
                        </div>
                      )}

                      {legendId === layer.id && legend && (
                        <div className="eco-layer-legend">
                          <img src={legend} alt={`${layer.label} legend`} />
                        </div>
                      )}
                    </div>
                  )
                })}
              </section>
            ))}
          </div>
        </aside>
      )}

      <button
        type="button"
        className="fit-map-button"
        disabled={!data?.features.length}
        onClick={() => {
          const map = mapRef.current
          if (map) fitToCollection(map, dataRef.current)
        }}
        title="Fit map to current H3 results"
      >
        Fit results
      </button>

      {hover && (
        <div className="map-hover-card">
          <span>{METRIC_LABELS[metric]}</span>
          <strong>{Math.round(clamp01(hover.value) * 100)}%</strong>
          <code>{hover.h3}</code>
          <i className={hover.synthetic ? '' : 'real'}>{hover.synthetic ? 'DEMO' : 'EVIDENCE'}</i>
        </div>
      )}

      {(inspectPoint || inspectionLoading) && (
        <aside className="eco-inspect-card">
          <header>
            <div>
              <strong>Inspect</strong>
              <span>{inspectPoint ? `${inspectPoint.lat.toFixed(5)}, ${inspectPoint.lng.toFixed(5)}` : 'Map point'}</span>
            </div>
            <button type="button" onClick={() => { setInspectPoint(null); setInspection([]) }}>×</button>
          </header>
          {inspectionLoading && <p className="eco-inspect-loading">Querying active WMS layers…</p>}
          {!inspectionLoading && inspection.length === 0 && (
            <p className="eco-inspect-empty">Enable a queryable layer such as AR5, SR16, NGU, ecosystems or Artskart, then click the map.</p>
          )}
          {!inspectionLoading && inspection.map(result => (
            <section key={result.layerId} className={result.ok ? '' : 'failed'}>
              <h5>{result.label}<small>{result.provider}</small></h5>
              <pre>{result.body}</pre>
            </section>
          ))}
        </aside>
      )}

      <div className="map-coordinate-readout">
        <span>{cursor ? `${cursor[1].toFixed(5)}° N` : `${center[1].toFixed(5)}° N`}</span>
        <span>{cursor ? `${cursor[0].toFixed(5)}° E` : `${center[0].toFixed(5)}° E`}</span>
        <b>EPSG:3857 / WGS84 cursor</b>
      </div>

      <div className="map-center-reticle" aria-hidden="true"><span /></div>
    </div>
  )
}
