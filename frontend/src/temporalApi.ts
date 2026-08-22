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
