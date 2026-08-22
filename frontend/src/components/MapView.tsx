import { useEffect, useRef } from 'react'
import maplibregl, { Map } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { ForecastCollection, ForecastFeature } from '../api'

export type MapMetric = 'combined' | 'habitat' | 'fruiting' | 'confidence'

type Props = {
  data: ForecastCollection | null
  center: [number, number]
  metric: MapMetric
  selectedH3?: string | null
  onSelect?: (feature: ForecastFeature | null) => void
}

const SOURCE = 'forecast-cells'
const FILL_LAYER = 'forecast-fill'
const SELECTED_LAYER = 'forecast-selected'

function metricExpression(metric: MapMetric) {
  return [
    'interpolate', ['linear'], ['coalesce', ['get', metric], 0],
    0, '#18251f',
    0.18, '#3d4b32',
    0.38, '#7a713a',
    0.58, '#8da447',
    0.78, '#55c66f',
    1, '#37f28a',
  ] as any
}

export default function MapView({ data, center, metric, selectedH3, onSelect }: Props) {
  const container = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<Map | null>(null)
  const dataRef = useRef<ForecastCollection | null>(data)
  const selectRef = useRef(onSelect)

  useEffect(() => { dataRef.current = data }, [data])
  useEffect(() => { selectRef.current = onSelect }, [onSelect])

  useEffect(() => {
    if (!container.current || mapRef.current) return

    const map = new maplibregl.Map({
      container: container.current,
      style: 'https://demotiles.maplibre.org/style.json',
      center,
      zoom: 9.8,
      pitch: 0,
      attributionControl: false,
    })

    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right')
    map.addControl(new maplibregl.ScaleControl({ maxWidth: 110, unit: 'metric' }), 'bottom-right')
    map.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right')

    map.on('load', () => {
      map.addSource(SOURCE, {
        type: 'geojson',
        data: dataRef.current || { type: 'FeatureCollection', features: [] },
      })

      map.addLayer({
        id: FILL_LAYER,
        type: 'fill',
        source: SOURCE,
        paint: {
          'fill-color': metricExpression(metric),
          'fill-opacity': ['case', ['get', 'synthetic_habitat'], 0.50, 0.76],
          'fill-outline-color': 'rgba(222,255,235,.34)',
        },
      })

      map.addLayer({
        id: SELECTED_LAYER,
        type: 'line',
        source: SOURCE,
        filter: ['==', ['get', 'h3'], selectedH3 || ''] as any,
        paint: {
          'line-color': '#ecfff4',
          'line-width': 3,
          'line-opacity': 0.95,
        },
      })

      map.on('mouseenter', FILL_LAYER, () => { map.getCanvas().style.cursor = 'pointer' })
      map.on('mouseleave', FILL_LAYER, () => { map.getCanvas().style.cursor = '' })
      map.on('click', FILL_LAYER, event => {
        const h3 = String(event.features?.[0]?.properties?.h3 || '')
        const feature = dataRef.current?.features.find(item => item.properties.h3 === h3) || null
        selectRef.current?.(feature)
      })

      map.on('click', event => {
        const hits = map.queryRenderedFeatures(event.point, { layers: [FILL_LAYER] })
        if (hits.length === 0) selectRef.current?.(null)
      })
    })

    mapRef.current = map
    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const update = () => {
      const source = map.getSource(SOURCE) as maplibregl.GeoJSONSource | undefined
      source?.setData(data || { type: 'FeatureCollection', features: [] })
      map.easeTo({ center, duration: 450 })
    }
    if (map.isStyleLoaded()) update()
    else map.once('load', update)
  }, [data, center])

  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const update = () => {
      if (map.getLayer(FILL_LAYER)) map.setPaintProperty(FILL_LAYER, 'fill-color', metricExpression(metric))
    }
    if (map.isStyleLoaded()) update()
    else map.once('load', update)
  }, [metric])

  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const update = () => {
      if (map.getLayer(SELECTED_LAYER)) map.setFilter(SELECTED_LAYER, ['==', ['get', 'h3'], selectedH3 || ''] as any)
    }
    if (map.isStyleLoaded()) update()
    else map.once('load', update)
  }, [selectedH3])

  return <div ref={container} className="map" />
}
