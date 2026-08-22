import { useEffect, useMemo, useState } from 'react'
import type { DataMode, ForecastCollection, ForecastFeature, ForecastProperties } from '../api'
import type { MapMetric } from './MapView'

type DockTab = 'hotspots' | 'compare' | 'saved'

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

export default function AnalysisDock({ data, selectedCell, metric, context, onSelectCell, onApplySearch }: Props) {
  const [tab, setTab] = useState<DockTab>('hotspots')
  const [pinned, setPinned] = useState<PinnedCell[]>(() => readStored<PinnedCell[]>(PIN_STORAGE, []))
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>(() => readStored<SavedSearch[]>(SEARCH_STORAGE, []))
  const [searchName, setSearchName] = useState('')

  useEffect(() => { persist(PIN_STORAGE, pinned) }, [pinned])
  useEffect(() => { persist(SEARCH_STORAGE, savedSearches) }, [savedSearches])

  const ranked = useMemo(() => {
    if (!data?.features.length) return []
    return [...data.features]
      .sort((a, b) => metricValue(b.properties, metric) - metricValue(a.properties, metric))
      .slice(0, 10)
  }, [data, metric])

  const currentPinId = selectedCell ? `${selectedCell.properties.species}:${selectedCell.properties.h3}` : ''
  const isPinned = Boolean(currentPinId && pinned.some(item => item.id === currentPinId))

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

  return (
    <section className="analysis-dock glass-panel">
      <div className="analysis-dock-head">
        <div>
          <div className="section-kicker">ANALYSIS WORKBENCH</div>
          <strong>Rank, compare and revisit</strong>
        </div>
        <div className="dock-tabs" role="tablist" aria-label="Analysis tools">
          <button type="button" className={tab === 'hotspots' ? 'active' : ''} onClick={() => setTab('hotspots')}>Hotspots</button>
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
