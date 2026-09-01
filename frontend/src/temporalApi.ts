import { getApiBaseUrl } from './api'

export type TemporalPoint = {
  time: string
  air_temperature_c: number
  relative_humidity_pct: number
  wind_speed_mps: number | null
  precipitation_mm: number
  precipitation_window_hours: number
  precipitation_rate_mm_h: number
  fruiting_score: number
  drivers: string[]
}

export type TemporalDay = {
  date: string
  mean_fruiting_score: number
  peak_fruiting_score: number
  ranking_score: number
  best_time: string
  temperature_mean_c: number
  humidity_mean_pct: number
  precipitation_total_mm: number
  sample_count: number
  drivers: string[]
}

export type TemporalForecast = {
  source: string
  generated_from: string | null
  horizon_days: number
  species: string
  center: [number, number]
  species_specific_weather_model: boolean
  interpretation: string
  points: TemporalPoint[]
  days: TemporalDay[]
  best_day: TemporalDay | null
  model: string
  warning: string
}

export type SpatialWeatherNode = {
  h3: string
  center: [number, number]
  forecast: TemporalForecast | null
  cached: boolean
  error: string | null
}

export type SpatialTemporalCell = {
  h3: string
  center: [number, number]
  weather_node_h3: string
  weather_node_distance_km: number
}

export type SpatialTemporalForecast = {
  species: string
  center: [number, number]
  radius_km: number
  h3_resolution: number
  cell_count: number
  species_specific_weather_model: boolean
  interpretation: string
  sampling: {
    method: string
    assignment: string
    requested_weather_nodes: number
    successful_weather_nodes: number
    concurrency_limit: number
    cache_ttl_seconds: number
  }
  weather_nodes: SpatialWeatherNode[]
  cells: SpatialTemporalCell[]
  data_quality: {
    label: 'high' | 'moderate' | 'limited'
    weather_node_coverage_ratio: number
    max_assignment_distance_km: number | null
    meaning: string
  }
  scientific_guardrail: string
}

export type ObservedWeatherDay = {
  source_id: string
  reference_time: string
  value_mm: number
  quality_code: number | string | null
  time_offset: string | null
  time_resolution: string | null
}

export type ObservedWeatherHistory = {
  available: boolean
  provider: string
  observed: boolean
  reason?: string
  center?: [number, number]
  source?: {
    id: string
    name: string | null
    distance_km: number | null
  }
  candidate_sources?: Array<{
    id: string
    name: string | null
    distance_km: number | null
  }>
  element?: string
  daily_standard_periods?: ObservedWeatherDay[]
  antecedent_precip_24h_standard_mm?: number | null
  antecedent_precip_72h_standard_mm?: number | null
  antecedent_precip_168h_standard_mm?: number | null
  latest_reference_time?: string | null
  data_quality?: {
    daily_periods_available: number
    requested_history_days: number
    source_distance_km: number | null
    meaning: string
  }
  aggregation_semantics?: string
  scientific_guardrail?: string
  probability_claim_allowed: false
}

async function requestJson(url: string): Promise<unknown> {
  if (window.mykoDesktop?.isDesktop) {
    const result = await window.mykoDesktop.httpRequest(url, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    })
    if (!result.ok) {
      let detail = `Temporal API error ${result.status}`
      try {
        const parsed = JSON.parse(result.body || '{}') as { detail?: string }
        if (parsed.detail) detail = parsed.detail
      } catch {
        // Keep status-based message.
      }
      throw new Error(detail)
    }
    return JSON.parse(result.body || 'null')
  }

  const response = await fetch(url, { headers: { Accept: 'application/json' } })
  if (!response.ok) {
    const parsed = await response.json().catch(() => null) as { detail?: string } | null
    throw new Error(parsed?.detail || `Temporal API error ${response.status}`)
  }
  return response.json()
}

export async function fetchTemporalForecast(
  lat: number,
  lon: number,
  species: string,
  days = 10,
): Promise<TemporalForecast> {
  const base = getApiBaseUrl()
  if (!base) throw new Error('Temporal forecast requires the MykoKnoks HTTPS API.')

  const params = new URLSearchParams({
    lat: String(lat),
    lon: String(lon),
    species,
    days: String(Math.max(1, Math.min(14, Math.round(days)))),
  })
  return await requestJson(`${base}/api/v1/temporal?${params}`) as TemporalForecast
}

export async function fetchSpatialTemporalForecast(
  lat: number,
  lon: number,
  radiusKm: number,
  resolution: number,
  species: string,
  days = 10,
  maxWeatherNodes = 9,
): Promise<SpatialTemporalForecast> {
  const base = getApiBaseUrl()
  if (!base) throw new Error('Spatial temporal forecast requires the MykoKnoks HTTPS API.')

  const params = new URLSearchParams({
    lat: String(lat),
    lon: String(lon),
    radius_km: String(radiusKm),
    resolution: String(resolution),
    species,
    days: String(Math.max(1, Math.min(14, Math.round(days)))),
    max_weather_nodes: String(Math.max(1, Math.min(16, Math.round(maxWeatherNodes)))),
  })
  return await requestJson(`${base}/api/v1/temporal/cells?${params}`) as SpatialTemporalForecast
}

export async function fetchObservedWeatherHistory(
  lat: number,
  lon: number,
  days = 14,
): Promise<ObservedWeatherHistory> {
  const base = getApiBaseUrl()
  if (!base) throw new Error('Observed weather requires the MykoKnoks HTTPS API.')

  const params = new URLSearchParams({
    lat: String(lat),
    lon: String(lon),
    days: String(Math.max(7, Math.min(31, Math.round(days)))),
  })
  return await requestJson(`${base}/api/v1/observed-weather?${params}`) as ObservedWeatherHistory
}
