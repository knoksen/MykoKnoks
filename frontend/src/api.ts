import { cellToBoundary, getHexagonEdgeLengthAvg, gridDisk, latLngToCell } from 'h3-js'

export type DataMode = 'demo' | 'live' | 'store'

export type ForecastProperties = {
  h3: string
  species: string
  habitat: number
  fruiting: number
  combined: number
  confidence: number
  drivers: string[]
  synthetic_habitat: boolean
  data_mode: DataMode
  provenance: string[]
  source_warnings: string[]
  elevation_m?: number | null
  terrain?: string | null
}

export type ForecastFeature = {
  type: 'Feature'
  id?: string
  geometry: { type: 'Polygon'; coordinates: number[][][] }
  properties: ForecastProperties
}

export type ForecastCollection = {
  type: 'FeatureCollection'
  features: ForecastFeature[]
  metadata?: Record<string, unknown>
}

export type SourceDescriptor = {
  id: string
  name: string
  organisation: string
  kind: string
  endpoint: string
  role: string
  live: boolean
  license?: string | null
}

export type ApiHealth = {
  status: string
  service?: string
  version?: string
  root_path?: string
}

const STORAGE_KEY = 'mykoknoks.apiBaseUrl'
const BUILD_BASE = normalizeBase(import.meta.env.VITE_API_BASE_URL?.trim() || '')

function normalizeBase(value: string) {
  return value.trim().replace(/\/+$/, '')
}

function storedBase() {
  try {
    return normalizeBase(window.localStorage.getItem(STORAGE_KEY) || '')
  } catch {
    return ''
  }
}

export function getApiBaseUrl() {
  return storedBase() || BUILD_BASE
}

export function setApiBaseUrl(value: string) {
  const normalized = normalizeBase(value)
  try {
    if (normalized) window.localStorage.setItem(STORAGE_KEY, normalized)
    else window.localStorage.removeItem(STORAGE_KEY)
  } catch {
    // WebView privacy/storage restrictions should never make the map unusable.
  }
  return normalized
}

export function hasConfiguredApi() {
  return Boolean(getApiBaseUrl())
}

export async function checkApiHealth(candidate?: string): Promise<ApiHealth> {
  const base = normalizeBase(candidate || getApiBaseUrl())
  if (!base) throw new Error('Ingen API-adresse er konfigurert.')

  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), 12000)
  try {
    const response = await fetch(`${base}/health`, {
      headers: { Accept: 'application/json' },
      signal: controller.signal,
    })
    if (!response.ok) throw new Error(`Health check feilet med HTTP ${response.status}.`)
    return response.json()
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('API-et svarte ikke innen 12 sekunder.')
    }
    throw error
  } finally {
    window.clearTimeout(timeout)
  }
}

function clamp01(value: number) {
  return Math.max(0, Math.min(1, value))
}

function hash01(value: string, salt: number) {
  let h = 2166136261 ^ salt
  for (let i = 0; i < value.length; i += 1) {
    h ^= value.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return (h >>> 0) / 4294967295
}

function demoCells(
  lat: number,
  lon: number,
  radiusKm: number,
  species: string,
  resolution: number,
): ForecastCollection {
  const center = latLngToCell(lat, lon, resolution)
  const edge = Math.max(0.02, getHexagonEdgeLengthAvg(resolution, 'km'))
  const ring = Math.min(18, Math.max(1, Math.ceil(radiusKm / (edge * 1.7))))
  const cells = gridDisk(center, ring)

  const features: ForecastFeature[] = cells.map(cell => {
    const habitat = clamp01(0.2 + hash01(cell, 11) * 0.75)
    const fruiting = clamp01(0.30 + hash01(cell, 29) * 0.62)
    const combined = habitat * fruiting
    const boundary = cellToBoundary(cell).map(([bLat, bLon]) => [bLon, bLat])
    boundary.push(boundary[0])
    return {
      type: 'Feature',
      id: cell,
      geometry: { type: 'Polygon', coordinates: [boundary] },
      properties: {
        h3: cell,
        species,
        habitat,
        fruiting,
        combined,
        confidence: 0.30,
        drivers: ['standalone mobile demo', 'deterministic H3 habitat proxy'],
        synthetic_habitat: true,
        data_mode: 'demo',
        provenance: ['MykoKnoks Android standalone engine'],
        source_warnings: ['Demo er syntetisk. Koble til HTTPS-API for live/store.'],
        elevation_m: null,
        terrain: null,
      },
    }
  })

  return {
    type: 'FeatureCollection',
    features,
    metadata: {
      standalone: true,
      center: [lon, lat],
      radius_km: radiusKm,
      h3_resolution: resolution,
      warning: 'Synthetic standalone mode. Not evidence of species presence.',
    },
  }
}

export async function fetchCells(
  lat: number,
  lon: number,
  radiusKm: number,
  species: string,
  dataMode: DataMode,
  resolution: number,
): Promise<ForecastCollection> {
  // Demo is deliberately local. The app remains useful even when the server is down.
  if (dataMode === 'demo') return demoCells(lat, lon, radiusKm, species, resolution)

  const base = getApiBaseUrl()
  if (!base) {
    throw new Error('Live/store krever MykoKnoks HTTPS-API. Åpne Server connection og koble til først.')
  }

  const params = new URLSearchParams({
    lat: String(lat),
    lon: String(lon),
    radius_km: String(radiusKm),
    species,
    data_mode: dataMode,
    resolution: String(resolution),
  })
  const response = await fetch(`${base}/api/v1/cells?${params}`)
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail || `API error ${response.status}`)
  }
  return response.json()
}

const OFFLINE_SOURCES: SourceDescriptor[] = [
  { id: 'artskart', name: 'Artskart', organisation: 'Artsdatabanken', kind: 'occurrences', endpoint: 'public API', role: 'species observations', live: false },
  { id: 'met', name: 'Locationforecast', organisation: 'MET Norway', kind: 'weather', endpoint: 'api.met.no', role: 'forecast weather', live: false },
  { id: 'ar5', name: 'AR5', organisation: 'NIBIO', kind: 'land resources', endpoint: 'WMS', role: 'habitat/land cover', live: false },
  { id: 'sr16', name: 'SR16', organisation: 'NIBIO', kind: 'forest', endpoint: 'WMS', role: 'tree/forest structure', live: false },
  { id: 'dtm', name: 'Terrain', organisation: 'Kartverket', kind: 'terrain', endpoint: 'Geonorge', role: 'elevation/terrain', live: false },
  { id: 'ngu', name: 'Løsmasser', organisation: 'NGU', kind: 'geology', endpoint: 'WMS/OGC', role: 'substrate', live: false },
]

export async function fetchSources(): Promise<SourceDescriptor[]> {
  const base = getApiBaseUrl()
  if (!base) return OFFLINE_SOURCES

  const response = await fetch(`${base}/api/v1/sources`)
  if (!response.ok) throw new Error(`Source API error ${response.status}`)
  return response.json()
}
