import { useEffect, useRef } from 'react'
import maplibregl, { Map } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { ForecastCollection } from '../api'

type Props = {
  data: ForecastCollection | null
  center: [number, number]
}

const SOURCE = 'forecast-cells'

const ENTITIES: Record<string, string> = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  "'": '&#39;',
  '"': '&quot;',
}

function esc(value: unknown) {
  return String(value ?? '').replace(/[&<>'"]/g, char => ENTITIES[char] || char)
}

export default function MapView({ data, center }: Props) {
  const container = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<Map | null>(null)

  useEffect(() => {
    if (!container.current || mapRef.current) return
    const map = new maplibregl.Map({
      container: container.current,
      style: 'https://demotiles.maplibre.org/style.json',
      center,
      zoom: 9.8,
    })
    map.addControl(new maplibregl.NavigationControl(), 'top-right')
    map.on('load', () => {
      map.addSource(SOURCE, {
        type: 'geojson',
        data: data || { type: 'FeatureCollection', features: [] },
      })
      map.addLayer({
        id: 'forecast-fill',
        type: 'fill',
        source: SOURCE,
        paint: {
          'fill-color': [
            'interpolate', ['linear'], ['get', 'combined'],
            0, '#25332d',
            0.25, '#7c6f3e',
            0.5, '#8e9a45',
            0.75, '#4fa85d',
            1, '#33d17a',
          ],
          'fill-opacity': [
            'case', ['get', 'synthetic_habitat'], 0.46, 0.72,
          ],
          'fill-outline-color': '#d8f3dc',
        },
      })
      map.on('click', 'forecast-fill', event => {
        const feature = event.features?.[0]
        if (!feature) return
        const p = feature.properties as Record<string, unknown>
        let provenance: unknown = p.provenance
        try {
          if (typeof provenance === 'string') provenance = JSON.parse(provenance)
        } catch { /* MapLibre may stringify arrays */ }
        const sourceText = Array.isArray(provenance) ? provenance.join(', ') : String(provenance || 'n/a')
        new maplibregl.Popup()
          .setLngLat(event.lngLat)
          .setHTML(`
            <div class="popup-title">${esc(p.species)}</div>
            <div class="popup-grid">
              <span>Combined</span><b>${Number(p.combined).toFixed(2)}</b>
              <span>Habitat</span><b>${Number(p.habitat).toFixed(2)}</b>
              <span>Fruiting</span><b>${Number(p.fruiting).toFixed(2)}</b>
              <span>Confidence</span><b>${Number(p.confidence).toFixed(2)}</b>
              <span>Elevation</span><b>${Number(p.elevation_m || 0).toFixed(0)} m</b>
              <span>Terrain</span><b>${esc(p.terrain || 'n/a')}</b>
            </div>
            <div class="popup-source">${esc(sourceText)}</div>
          `)
          .addTo(map)
      })
    })
    mapRef.current = map
    return () => { map.remove(); mapRef.current = null }
  }, [])

  useEffect(() => {
    const map = mapRef.current
    if (!map || !data) return
    const update = () => {
      const source = map.getSource(SOURCE) as maplibregl.GeoJSONSource | undefined
      source?.setData(data)
      map.easeTo({ center, duration: 500 })
    }
    if (map.isStyleLoaded()) update()
    else map.once('load', update)
  }, [data, center])

  return <div ref={container} className="map" />
}
