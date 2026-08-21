import { FormEvent, useEffect, useMemo, useState } from 'react'
import {
  fetchCells,
  fetchSources,
  standaloneMode,
  type DataMode,
  type ForecastCollection,
  type SourceDescriptor,
} from './api'
import MapView from './components/MapView'

const DEFAULT_LAT = 58.735
const DEFAULT_LON = 5.647

export default function App() {
  const [lat, setLat] = useState(DEFAULT_LAT)
  const [lon, setLon] = useState(DEFAULT_LON)
  const [radius, setRadius] = useState(3)
  const [resolution, setResolution] = useState(9)
  const [species, setSpecies] = useState('Psilocybe semilanceata')
  const [dataMode, setDataMode] = useState<DataMode>('demo')
  const [data, setData] = useState<ForecastCollection | null>(null)
  const [sources, setSources] = useState<SourceDescriptor[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const stats = useMemo(() => {
    if (!data?.features.length) return null
    const values = data.features.map(f => f.properties.combined)
    const real = data.features.filter(f => !f.properties.synthetic_habitat).length
    return {
      cells: values.length,
      real,
      max: Math.max(...values),
      mean: values.reduce((a, b) => a + b, 0) / values.length,
    }
  }, [data])

  async function load() {
    setLoading(true)
    setError('')
    try {
      setData(await fetchCells(lat, lon, radius, species, dataMode, resolution))
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
    void fetchSources().then(setSources).catch(() => undefined)
  }, [])

  function submit(e: FormEvent) {
    e.preventDefault()
    void load()
  }

  function useMyLocation() {
    if (!navigator.geolocation) {
      setError('Posisjon er ikke tilgjengelig på denne enheten.')
      return
    }
    setLoading(true)
    navigator.geolocation.getCurrentPosition(
      position => {
        setLat(position.coords.latitude)
        setLon(position.coords.longitude)
        setLoading(false)
      },
      err => {
        setError(`Kunne ikke hente posisjon: ${err.message}`)
        setLoading(false)
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 30000 },
    )
  }

  function changeMode(mode: DataMode) {
    setDataMode(mode)
    if (mode === 'live') {
      setRadius(current => Math.min(current, 1))
      setResolution(9)
    }
  }

  return (
    <main>
      <header className="hero">
        <div>
          <div className="eyebrow">NORDIC ECOLOGICAL INTELLIGENCE</div>
          <h1>MykoKnoks</h1>
          <p className="lead">Observed nature + terrain + weather → auditable habitat intelligence.</p>
        </div>
        <div className="badge">v0.2 · H3 · PostGIS · Norway data engine</div>
      </header>

      <section className="layout">
        <aside className="panel">
          <h2>Forecast explorer</h2>
          <form onSubmit={submit}>
            <label>
              Species
              <input value={species} onChange={e => setSpecies(e.target.value)} />
            </label>
            <div className="twocol">
              <label>
                Latitude
                <input
                  type="number"
                  step="0.001"
                  value={lat}
                  onChange={e => setLat(Number(e.target.value))}
                />
              </label>
              <label>
                Longitude
                <input
                  type="number"
                  step="0.001"
                  value={lon}
                  onChange={e => setLon(Number(e.target.value))}
                />
              </label>
            </div>
            <div className="twocol">
              <label>
                Data mode
                <select value={dataMode} onChange={e => changeMode(e.target.value as DataMode)}>
                  <option value="demo">Demo</option>
                  <option value="live">Live Norway probe</option>
                  <option value="store">PostGIS feature store</option>
                </select>
              </label>
              <label>
                H3 resolution
                <select value={resolution} onChange={e => setResolution(Number(e.target.value))}>
                  <option value={8}>8 · regional</option>
                  <option value={9}>9 · local</option>
                  <option value={10}>10 · fine</option>
                </select>
              </label>
            </div>
            <label>
              Radius: {radius} km
              <input
                type="range"
                min="0.3"
                max={dataMode === 'live' ? '1.2' : '15'}
                step="0.1"
                value={radius}
                onChange={e => setRadius(Number(e.target.value))}
              />
            </label>
            <div className="action-row">
              <button type="button" className="secondary" disabled={loading} onClick={useMyLocation}>Use my position</button>
              <button disabled={loading}>{loading ? 'Calculating…' : 'Run forecast'}</button>
            </div>
            {standaloneMode && <small className="standalone-note">Android standalone: Demo works locally. Live/store activates when a public HTTPS backend is configured.</small>}
          </form>

          {error && <div className="error">{error}</div>}

          {stats && (
            <div className="stats four">
              <div><span>Cells</span><strong>{stats.cells}</strong></div>
              <div><span>Real</span><strong>{stats.real}</strong></div>
              <div><span>Mean</span><strong>{stats.mean.toFixed(2)}</strong></div>
              <div><span>Peak</span><strong>{stats.max.toFixed(2)}</strong></div>
            </div>
          )}

          <div className="mode-explainer">
            <strong>{dataMode === 'demo' ? 'Demo mode' : dataMode === 'live' ? 'Live mode' : 'Feature-store mode'}</strong>
            <p>
              {dataMode === 'demo'
                ? 'Deterministic synthetic habitat; useful for UI and pipeline testing.'
                : dataMode === 'live'
                  ? 'Queries real Kartverket terrain/elevation per H3 cell with a strict request cap.'
                  : 'Serves pre-ingested H3 environmental features from PostGIS; cache misses stay visibly marked.'}
            </p>
          </div>

          <div className="source-list">
            <div className="section-label">CONNECTED DATA STACK</div>
            {sources.slice(0, 7).map(source => (
              <div className="source-row" key={source.id}>
                <span className="source-dot" />
                <div><strong>{source.name}</strong><small>{source.organisation} · {source.kind}</small></div>
              </div>
            ))}
          </div>

          <div className="notice">
            <strong>Scientific safety</strong>
            <p>Suitability is not confirmed presence, edibility or species identification. Every real-data cell carries provenance and confidence.</p>
          </div>
        </aside>
        <section className="map-shell"><MapView data={data} center={[lon, lat]} /></section>
      </section>
    </main>
  )
}
