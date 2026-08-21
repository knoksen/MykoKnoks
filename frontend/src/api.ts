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

const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function fetchCells(
  lat: number,
  lon: number,
  radiusKm: number,
  species: string,
  dataMode: DataMode,
  resolution: number,
): Promise<ForecastCollection> {
  const params = new URLSearchParams({
    lat: String(lat),
    lon: String(lon),
    radius_km: String(radiusKm),
    species,
    data_mode: dataMode,
    resolution: String(resolution),
  })
  const response = await fetch(`${BASE}/api/v1/cells?${params}`)
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail || `API error ${response.status}`)
  }
  return response.json()
}

export async function fetchSources(): Promise<SourceDescriptor[]> {
  const response = await fetch(`${BASE}/api/v1/sources`)
  if (!response.ok) throw new Error(`Source API error ${response.status}`)
  return response.json()
}
