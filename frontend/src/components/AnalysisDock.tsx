import { useEffect, useMemo, useState } from 'react'
import type { DataMode, ForecastCollection, ForecastFeature, ForecastProperties } from '../api'
import {
  fetchSpatialTemporalForecast,
  fetchTemporalForecast,
  type SpatialTemporalForecast,
  type TemporalDay,
  type TemporalForecast,
} from '../temporalApi'
import type { MapMetric } from './MapView'

type DockTab = 'hotspots' | 'timeline' | 'compare' | 'saved'

export type SearchContext = {
  lat: number
  lon: number
  radius: number
  resolution: number
  species: string
  dataMode: DataMode
}

export type SavedSearch = SearchContext & {
  id: string
  name: string
  savedAt: string
}

export type TemporalMapCell = {
  temporal: number
  combined: number
  spatial: boolean
  weatherNodeDistanceKm: number | null
}

export type TemporalMapState = {
  date: string
  label: string
  cells: Record<string, TemporalMapCell>
  dataSupport: string
  successfulWeatherNodes: number
  requestedWeatherNodes: number
}

type PinnedCell = Pick<ForecastProperties,
  'h3' | 'species' | 'combined' | 'habitat' | 'fruiting' | 'confidence' |
  'elevation_m' | 'terrain' | 'synthetic_habitat' | 'data_mode'
> & {
  id: string
  pinnedAt: string
}

type Props = {
  data: ForecastCollection | null
  selectedCell: ForecastFeature | null
  metric: MapMetric
  context: SearchContext
  onSelectCell: (feature: ForecastFeature | null) => void
  onApplySearch: (saved: SavedSearch) => void
  onTemporalMapChange?: (state: TemporalMapState | null) => void
}

const PIN_STORAGE = 'mykoknoks.v05.pinnedCells'
const SEARCH_STORAGE = 'mykoknoks.v05.savedSearches'

function pct(value: number | null | undefined) {
  return `${Math.round(Math.max(0, Math.min(1, Number(value || 0))) * 100)}%`
}

function readStored<T>(key: string, fallback: T): T {
  try {
    const raw = window.localStorage.getItem(key)
    return raw ? JSON.parse(raw) as T : fallback
  } catch {
    return fallback
  }
}

function persist(key: string, value: unknown) {
  try {
    window.localStorage.setItem(key, JSON.stringify(value))
  } catch {
    // Storage failures should not break analysis controls.
  }
}

function metricValue(properties: ForecastProperties, metric: MapMetric) {
  return Number(properties[metric] || 0)
}

function cellSnapshot(feature: ForecastFeature): PinnedCell {
  const p = feature.properties
  return {
    id: `${p.species}:${p.h3}`,
    h3: p.h3,
    species: p.species,
    combined: p.combined,
    habitat: p.habitat,
    fruiting: p.fruiting,
    confidence: p.confidence,
    elevation_m: p.elevation_m,
    terrain: p.terrain,
    synthetic_habitat: p.synthetic_habitat,
    data_mode: p.data_mode,
    pinnedAt: new Date().toISOString(),
  }
}

function displayDate(day: TemporalDay) {
  return new Date(`${day.date}T12:00:00Z`).toLocaleDateString([], {
    weekday: 'short',
    day: '2-digit',
    month: 'short',
  })
}

function sparklinePoints(values: number[], width = 240, height = 54): string {
  if (!values.length) return ''
  const xStep = values.length === 1 ? 0 : width / (values.length - 1)
  return values
    .map((value, index) => {
      const safe = Math.max(0, Math.min(1, Number(value || 0)))
      const x = index * xStep
      const y = height - safe * (height - 8) - 4
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
}

export default function AnalysisDock({
  data,
  selectedCell,
  metric,
  context,
  onSelectCell,
  onApplySearch,
  onTemporalMapChange,
}: Props) {
  const [tab, setTab] = useState<DockTab>('hotspots')
  const [pinned, setPinned] = useState<PinnedCell[]>(() => readStored<PinnedCell[]>(PIN_STORAGE, []))
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>(() => readStored<SavedSearch[]>(SEARCH_STORAGE, []))
  const [searchName, setSearchName] = useState('')
  const [temporal, setTemporal] = useState<TemporalForecast | null>(null)
  const [spatialTemporal, setSpatialTemporal] = useState<SpatialTemporalForecast | null>(null)
  const [temporalLoading, setTemporalLoading] = useState(false)
  const [temporalError, setTemporalError] = useState('')
  const [spatialTemporalError, setSpatialTemporalError] = useState('')
  const [temporalKey, setTemporalKey] = useState('')
  const [selectedDayDate, setSelectedDayDate] = useState('')
  const [playing, setPlaying] = useState(false)

  useEffect(() => { persist(PIN_STORAGE, pinned) }, [pinned])
  useEffect(() => { persist(SEARCH_STORAGE, savedSearches) }, [savedSearches])

  const ranked = useMemo(() => {
    if (!data?.features.length) return []
    return [...data.features]
      .sort((a, b) => metricValue(b.properties, metric) - metricValue(a.properties, metric))
      .slice(0, 10)
  }, [data, metric])

  const currentTemporalKey = [
    context.lat.toFixed(4),
    context.lon.toFixed(4),
    context.radius.toFixed(2),
    context.resolution,
    context.species,
  ].join(':')
  const selectedDay = temporal?.days.find(day => day.date === selectedDayDate)
    || temporal?.best_day
    || temporal?.days[0]
    || null
  const temporalStale = Boolean(temporal && temporalKey !== currentTemporalKey)

  const spatialAssignments = useMemo(
    () => new Map((spatialTemporal?.cells || []).map(item => [item.h3, item])),
    [spatialTemporal],
  )
  const spatialNodes = useMemo(
    () => new Map((spatialTemporal?.weather_nodes || []).map(item => [item.h3, item])),
    [spatialTemporal],
  )

  const temporalMapState = useMemo<TemporalMapState | null>(() => {
    if (!data?.features.length || !selectedDay || temporalStale) return null
    const cells: Record<string, TemporalMapCell> = {}
    for (const feature of data.features) {
      const assignment = spatialAssignments.get(feature.properties.h3)
      const node = assignment ? spatialNodes.get(assignment.weather_node_h3) : undefined
      const spatialDay = node?.forecast?.days.find(day => day.date === selectedDay.date)
      const temporalScore = Number(
        spatialDay?.peak_fruiting_score ?? selectedDay.peak_fruiting_score ?? 0,
      )
      cells[feature.properties.h3] = {
        temporal: temporalScore,
        combined: Number(feature.properties.habitat || 0) * temporalScore,
        spatial: Boolean(spatialDay),
        weatherNodeDistanceKm: assignment?.weather_node_distance_km ?? null,
      }
    }
    return {
      date: selectedDay.date,
      label: displayDate(selectedDay),
      cells,
      dataSupport: spatialTemporal?.data_quality.label || 'center fallback',
      successfulWeatherNodes: spatialTemporal?.sampling.successful_weather_nodes || 0,
      requestedWeatherNodes: spatialTemporal?.sampling.requested_weather_nodes || 0,
    }
  }, [data, selectedDay, temporalStale, spatialAssignments, spatialNodes, spatialTemporal])

  useEffect(() => {
    onTemporalMapChange?.(temporalMapState)
    return () => onTemporalMapChange?.(null)
  }, [temporalMapState, onTemporalMapChange])

  const temporalAreas = useMemo(() => {
    if (!data?.features.length || !temporalMapState) return []
    return [...data.features]
      .map(feature => {
        const cell = temporalMapState.cells[feature.properties.h3]
        return {
          feature,
          temporalScore: cell?.temporal ?? 0,
          weatherNodeDistanceKm: cell?.weatherNodeDistanceKm ?? null,
          spatial: Boolean(cell?.spatial),
          score: cell?.combined ?? 0,
        }
      })
      .sort((a, b) => b.score - a.score)
      .slice(0, 6)
  }, [data, temporalMapState])

  const selectedCellSeries = useMemo(() => {
    if (!temporal?.days.length || !selectedCell) return []
    const assignment = spatialAssignments.get(selectedCell.properties.h3)
    const node = assignment ? spatialNodes.get(assignment.weather_node_h3) : undefined
    return temporal.days.map(day => {
      const spatialDay = node?.forecast?.days.find(candidate => candidate.date === day.date)
      return {
        date: day.date,
        score: Number(spatialDay?.peak_fruiting_score ?? day.peak_fruiting_score ?? 0),
        spatial: Boolean(spatialDay),
      }
    })
  }, [temporal, selectedCell, spatialAssignments, spatialNodes])

  const currentPinId = selectedCell ? `${selectedCell.properties.species}:${selectedCell.properties.h3}` : ''
  const isPinned = Boolean(currentPinId && pinned.some(item => item.id === currentPinId))

  async function refreshTemporal() {
    setTemporalLoading(true)
    setTemporalError('')
    setSpatialTemporalError('')
    setPlaying(false)
    try {
      const [centerResult, spatialResult] = await Promise.allSettled([
        fetchTemporalForecast(context.lat, context.lon, context.species, 10),
        fetchSpatialTemporalForecast(
          context.lat,
          context.lon,
          context.radius,
          context.resolution,
          context.species,
          10,
          9,
        ),
      ])

      if (centerResult.status === 'rejected') throw centerResult.reason
      const result = centerResult.value
      setTemporal(result)
      setTemporalKey(currentTemporalKey)
      setSelectedDayDate(result.best_day?.date || result.days[0]?.date || '')

      if (spatialResult.status === 'fulfilled') {
        setSpatialTemporal(spatialResult.value)
      } else {
        setSpatialTemporal(null)
        setSpatialTemporalError(
          spatialResult.reason instanceof Error
            ? spatialResult.reason.message
            : String(spatialResult.reason),
        )
      }
    } catch (error) {
      setTemporalError(error instanceof Error ? error.message : String(error))
    } finally {
      setTemporalLoading(false)
    }
  }

  useEffect(() => {
    if (tab === 'timeline' && !temporal && !temporalLoading) void refreshTemporal()
  }, [tab])

  useEffect(() => {
    if (!playing || !temporal?.days.length) return
    const timer = window.setInterval(() => {
      setSelectedDayDate(current => {
        const index = temporal.days.findIndex(day => day.date === current)
        const next = index < 0 ? 0 : (index + 1) % temporal.days.length
        return temporal.days[next].date
      })
    }, 1300)
    return () => window.clearInterval(timer)
  }, [playing, temporal])

  function pinSelected() {
    if (!selectedCell || isPinned) return
    setPinned(current => [cellSnapshot(selectedCell), ...current].slice(0, 12))
    setTab('compare')
  }

  function saveCurrentSearch() {
    const clean = searchName.trim()
    const saved: SavedSearch = {
      ...context,
      id: `${Date.now()}-${context.lat.toFixed(4)}-${context.lon.toFixed(4)}`,
      name: clean || `${context.species} · ${context.lat.toFixed(3)}, ${context.lon.toFixed(3)}`,
      savedAt: new Date().toISOString(),
    }
    setSavedSearches(current => [saved, ...current].slice(0, 20))
    setSearchName('')
    setTab('saved')
  }

  const selectedDayIndex = Math.max(
    0,
    temporal?.days.findIndex(day => day.date === selectedDay?.date) ?? 0,
  )
  const sparkPoints = sparklinePoints(selectedCellSeries.map(item => item.score))

  return (
    <section className="analysis-dock glass-panel">
      <div className="analysis-dock-head">
        <div>
          <div className="section-kicker">ANALYSIS WORKBENCH</div>
          <strong>Rank, forecast, compare and revisit</strong>
        </div>
        <div className="dock-tabs" role="tablist" aria-label="Analysis tools">
          <button type="button" className={tab === 'hotspots' ? 'active' : ''} onClick={() => setTab('hotspots')}>Hotspots</button>
          <button type="button" className={tab === 'timeline' ? 'active' : ''} onClick={() => setTab('timeline')}>Timeline <span>MET</span></button>
          <button type="button" className={tab === 'compare' ? 'active' : ''} onClick={() => setTab('compare')}>Compare <span>{pinned.length}</span></button>
          <button type="button" className={tab === 'saved' ? 'active' : ''} onClick={() => setTab('saved')}>Saved <span>{savedSearches.length}</span></button>
        </div>
      </div>

      {tab === 'hotspots' && (
        <div className="dock-panel hotspots-panel">
          <div className="dock-panel-copy">
            <strong>Top cells by {metric === 'combined' ? 'suitability' : metric}</strong>
            <span>Ranking is calculated from the currently loaded H3 result set.</span>
          </div>
          <div className="hotspot-list">
            {ranked.length === 0 && <div className="dock-empty">Run a forecast to rank cells.</div>}
            {ranked.map((feature, index) => {
              const p = feature.properties
              const value = metricValue(p, metric)
              const selected = selectedCell?.properties.h3 === p.h3
              return (
                <button type="button" className={`hotspot-row ${selected ? 'selected' : ''}`} key={`${p.h3}-${p.species}`} onClick={() => onSelectCell(feature)}>
                  <span className="hotspot-rank">{String(index + 1).padStart(2, '0')}</span>
                  <span className="hotspot-main"><strong>{pct(value)}</strong><small>{p.h3}</small></span>
                  <span className="hotspot-bar"><i style={{ width: `${Math.max(2, value * 100)}%` }} /></span>
                  <span className={`evidence-chip ${p.synthetic_habitat ? '' : 'real'}`}>{p.synthetic_habitat ? 'demo' : 'evidence'}</span>
                </button>
              )
            })}
          </div>
        </div>
      )}

      {tab === 'timeline' && (
        <div className="dock-panel timeline-panel">
          <div className="timeline-head">
            <div>
              <strong>10-day fruiting weather window</strong>
              <span>MET Norway forecast → spatially sampled, explainable temperature / humidity / precipitation heuristic.</span>
            </div>
            <button type="button" disabled={temporalLoading} onClick={() => void refreshTemporal()}>{temporalLoading ? 'Loading…' : temporalStale ? 'Refresh changed location' : 'Refresh MET'}</button>
            <button type="button" disabled={!temporal?.days.length} onClick={() => setPlaying(value => !value)}>{playing ? 'Pause map' : 'Play days'}</button>
          </div>

          {temporalError && <div className="temporal-error">{temporalError}</div>}
          {spatialTemporalError && temporal && (
            <div className="temporal-stale">Spatial MET unavailable: {spatialTemporalError}. Area ranking is using center weather fallback.</div>
          )}
          {!temporal && temporalLoading && <div className="dock-empty">Loading MET Norway forecast timeline…</div>}
          {!temporal && !temporalLoading && !temporalError && <div className="dock-empty">Temporal forecast requires the connected HTTPS backend.</div>}

          {temporal && (
            <>
              {temporalStale && <div className="temporal-stale">Search location, radius, H3 resolution or species changed. Refresh to recalculate the timeline.</div>}
              {spatialTemporal && (
                <div className="temporal-stale">
                  Spatial weather · {spatialTemporal.data_quality.label} data support · {spatialTemporal.sampling.successful_weather_nodes}/{spatialTemporal.sampling.requested_weather_nodes} MET nodes · max assignment {spatialTemporal.data_quality.max_assignment_distance_km?.toFixed(1) ?? 'n/a'} km
                </div>
              )}
              <div className="timeline-days">
                {temporal.days.map(day => {
                  const active = selectedDay?.date === day.date
                  const best = temporal.best_day?.date === day.date
                  return (
                    <button type="button" key={day.date} className={`timeline-day ${active ? 'active' : ''}`} onClick={() => { setPlaying(false); setSelectedDayDate(day.date) }}>
                      <span>{displayDate(day)}</span>
                      <strong>{pct(day.peak_fruiting_score)}</strong>
                      <i><b style={{ height: `${Math.max(4, day.peak_fruiting_score * 100)}%` }} /></i>
                      <small>{day.temperature_mean_c.toFixed(1)}° · {Math.round(day.humidity_mean_pct)}% RH · {day.precipitation_total_mm.toFixed(1)} mm</small>
                      {best && <em>BEST DAY</em>}
                    </button>
                  )
                })}
              </div>

              {temporal.days.length > 1 && (
                <div className="timeline-playback">
                  <span>{playing ? 'Animating map' : 'Selected day'} · {selectedDay ? displayDate(selectedDay) : '—'}</span>
                  <input
                    aria-label="Forecast day"
                    type="range"
                    min="0"
                    max={Math.max(0, temporal.days.length - 1)}
                    step="1"
                    value={selectedDayIndex}
                    onChange={event => {
                      setPlaying(false)
                      setSelectedDayDate(temporal.days[Number(event.target.value)]?.date || '')
                    }}
                  />
                </div>
              )}

              {selectedDay && (
                <div className="temporal-detail-grid">
                  <div className="temporal-day-detail">
                    <div className="section-kicker">SELECTED DAY</div>
                    <strong>{displayDate(selectedDay)} · center peak {pct(selectedDay.peak_fruiting_score)}</strong>
                    <div className="temporal-metrics">
                      <span><b>{selectedDay.temperature_mean_c.toFixed(1)}°C</b> mean temp</span>
                      <span><b>{Math.round(selectedDay.humidity_mean_pct)}%</b> humidity</span>
                      <span><b>{selectedDay.precipitation_total_mm.toFixed(1)} mm</b> precipitation</span>
                      <span><b>{new Date(selectedDay.best_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</b> peak time</span>
                    </div>
                    <div className="tag-cloud">{selectedDay.drivers.map(driver => <span key={driver}>{driver}</span>)}</div>
                    {selectedCell && selectedCellSeries.length > 0 && (
                      <div className="temporal-sparkline">
                        <div className="section-kicker">SELECTED CELL · 10-DAY TRACE</div>
                        <svg viewBox="0 0 240 54" role="img" aria-label="Selected cell temporal suitability trace">
                          <polyline points={sparkPoints} fill="none" stroke="currentColor" strokeWidth="2.5" vectorEffect="non-scaling-stroke" />
                        </svg>
                        <small>
                          {selectedCell.properties.h3} · {selectedCellSeries.some(item => item.spatial) ? 'spatial MET node' : 'center fallback'}
                        </small>
                      </div>
                    )}
                  </div>

                  <div className="temporal-area-rank">
                    <div className="section-kicker">BEST AREA · SELECTED DAY</div>
                    {temporalAreas.length === 0 ? (
                      <span className="temporal-note">Run a spatial forecast to combine this day's fruiting window with H3 habitat.</span>
                    ) : temporalAreas.map((item, index) => (
                      <button type="button" key={item.feature.properties.h3} onClick={() => onSelectCell(item.feature)}>
                        <span>{index + 1}</span>
                        <code>{item.feature.properties.h3}</code>
                        <strong>{pct(item.score)}</strong>
                        <small>
                          {item.spatial ? `spatial ${pct(item.temporalScore)}` : `center ${pct(item.temporalScore)}`}
                          {item.weatherNodeDistanceKm == null ? '' : ` · node ${item.weatherNodeDistanceKm.toFixed(1)} km`}
                        </small>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div className="temporal-warning"><strong>Model boundary</strong><span>{spatialTemporal?.scientific_guardrail || temporal.warning}</span></div>
            </>
          )}
        </div>
      )}

      {tab === 'compare' && (
        <div className="dock-panel compare-panel">
          <div className="compare-actions">
            <div>
              <strong>Cell comparison</strong>
              <span>Pin up to 12 cells across runs. Snapshots remain local on this device.</span>
            </div>
            <button type="button" disabled={!selectedCell || isPinned} onClick={pinSelected}>{isPinned ? 'Pinned' : 'Pin selected cell'}</button>
          </div>
          {pinned.length === 0 ? (
            <div className="dock-empty">Select a map cell and pin it to build a comparison set.</div>
          ) : (
            <div className="compare-table-wrap">
              <table className="compare-table">
                <thead><tr><th>Cell</th><th>Suitability</th><th>Habitat</th><th>Fruiting</th><th>Confidence</th><th>Elevation</th><th>Mode</th><th /></tr></thead>
                <tbody>
                  {pinned.map(item => (
                    <tr key={item.id}>
                      <td><strong>{item.species}</strong><code>{item.h3}</code></td>
                      <td>{pct(item.combined)}</td>
                      <td>{pct(item.habitat)}</td>
                      <td>{pct(item.fruiting)}</td>
                      <td>{pct(item.confidence)}</td>
                      <td>{item.elevation_m == null ? 'n/a' : `${Math.round(item.elevation_m)} m`}</td>
                      <td><span className={`evidence-chip ${item.synthetic_habitat ? '' : 'real'}`}>{item.data_mode}</span></td>
                      <td><button type="button" className="table-remove" title="Remove comparison cell" onClick={() => setPinned(current => current.filter(candidate => candidate.id !== item.id))}>×</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {tab === 'saved' && (
        <div className="dock-panel saved-panel">
          <div className="save-search-row">
            <label>
              <span>Name current search</span>
              <input value={searchName} onChange={event => setSearchName(event.target.value)} placeholder={`${context.species} · ${context.lat.toFixed(3)}, ${context.lon.toFixed(3)}`} />
            </label>
            <button type="button" onClick={saveCurrentSearch}>Save current workspace</button>
          </div>
          <div className="saved-grid">
            {savedSearches.length === 0 && <div className="dock-empty">No saved searches yet.</div>}
            {savedSearches.map(saved => (
              <article className="saved-card" key={saved.id}>
                <div><strong>{saved.name}</strong><small>{saved.species}</small></div>
                <div className="saved-meta"><span>{saved.lat.toFixed(4)}, {saved.lon.toFixed(4)}</span><span>{saved.radius.toFixed(1)} km · H3 r{saved.resolution} · {saved.dataMode.toUpperCase()}</span></div>
                <div className="saved-actions">
                  <button type="button" onClick={() => onApplySearch(saved)}>Load</button>
                  <button type="button" className="ghost" onClick={() => setSavedSearches(current => current.filter(candidate => candidate.id !== saved.id))}>Delete</button>
                </div>
              </article>
            ))}
          </div>
        </div>
      )}
    </section>
  )
}
