import { useEffect, useRef, useState } from 'react'
import maplibregl, { Map } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { ForecastCollection, ForecastFeature } from '../api'

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

const SOURCE = 'forecast-cells'
const CENTER_SOURCE = 'search-center'
const FILL_LAYER = 'forecast-fill'
const LINE_LAYER = 'forecast-lines'
const HOVER_LAYER = 'forecast-hover'
const SELECTED_LAYER = 'forecast-selected'
const CENTER_LAYER = 'search-center-point'
const BASEMAP_STORAGE = 'mykoknoks.v07.basemap'

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
    // A storage failure should never prevent the map from starting.
  }
  return 'topo'
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

function fitToCollection(map: Map, data: ForecastCollection | null) {
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
  const mapRef = useRef<Map | null>(null)
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

  dataRef.current = data
  selectRef.current = onSelect
  metricRef.current = metric
  minScoreRef.current = minScore
  opacityRef.current = fillOpacity
  outlinesRef.current = showOutlines
  selectedRef.current = selectedH3 || ''
  centerRef.current = center

  function installAnalysisLayers(map: Map) {
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

    map.on('click', FILL_LAYER, event => {
      const h3 = String(event.features?.[0]?.properties?.h3 || '')
      const feature = dataRef.current?.features.find(item => item.properties.h3 === h3) || null
      selectRef.current?.(feature)
    })

    map.on('click', event => {
      if (!map.getLayer(FILL_LAYER)) return
      const hits = map.queryRenderedFeatures(event.point, { layers: [FILL_LAYER] })
      if (hits.length === 0) selectRef.current?.(null)
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
    <div className="map-pro-shell">
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

      <div className="map-coordinate-readout">
        <span>{cursor ? `${cursor[1].toFixed(5)}° N` : `${center[1].toFixed(5)}° N`}</span>
        <span>{cursor ? `${cursor[0].toFixed(5)}° E` : `${center[0].toFixed(5)}° E`}</span>
        <b>EPSG:3857 / WGS84 cursor</b>
      </div>

      <div className="map-center-reticle" aria-hidden="true"><span /></div>
    </div>
  )
}
