import { FormEvent, useEffect, useMemo, useState } from 'react'
import {
  checkApiHealth,
  fetchCells,
  fetchSources,
  getApiBaseUrl,
  setApiBaseUrl,
  type DataMode,
  type ForecastCollection,
  type ForecastFeature,
  type SourceDescriptor,
} from './api'
import MapView, { type MapMetric } from './components/MapView'

const DESKTOP_VERSION = '0.4.0'
const MOBILE_VERSION = '0.2.4'
const DEFAULT_LAT = 58.735
const DEFAULT_LON = 5.647
const ULTRA_API_CANDIDATE = 'https://knoksen.nova.usbx.me/mykoknoks-api'

type InspectorTab = 'cell' | 'sources' | 'system'

const MODE_COPY: Record<DataMode, { label: string; short: string; description: string }> = {
  demo: {
    label: 'Demo',
    short: 'LOCAL',
    description: 'Deterministic synthetic H3 surface for interface and pipeline testing.',
  },
  live: {
    label: 'Live',
    short: 'PROBE',
    description: 'Queries live terrain/environment services with a deliberately small request radius.',
  },
  store: {
    label: 'H3 Store',
    short: 'CACHE',
    description: 'Reads pre-ingested environmental features from the server-side H3 feature store.',
  },
}

const METRICS: Array<{ id: MapMetric; label: string }> = [
  { id: 'combined', label: 'Suitability' },
  { id: 'habitat', label: 'Habitat' },
  { id: 'fruiting', label: 'Fruiting' },
  { id: 'confidence', label: 'Confidence' },
]

function pct(value: number | null | undefined) {
  return `${Math.round(Math.max(0, Math.min(1, Number(value || 0))) * 100)}%`
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  const safe = Math.max(0, Math.min(1, value || 0))
  return (
    <div className="score-row">
      <div className="score-copy"><span>{label}</span><strong>{pct(safe)}</strong></div>
      <div className="score-track"><i style={{ width: `${safe * 100}%` }} /></div>
    </div>
  )
}

export default function App() {
  const isDesktop = Boolean(window.mykoDesktop?.isDesktop)
  const appVersion = isDesktop ? DESKTOP_VERSION : MOBILE_VERSION
  const [lat, setLat] = useState(DEFAULT_LAT)
  const [lon, setLon] = useState(DEFAULT_LON)
  const [radius, setRadius] = useState(3)
  const [resolution, setResolution] = useState(9)
  const [species, setSpecies] = useState('Psilocybe semilanceata')
  const [dataMode, setDataMode] = useState<DataMode>('demo')
  const [metric, setMetric] = useState<MapMetric>('combined')
  const [data, setData] = useState<ForecastCollection | null>(null)
  const [sources, setSources] = useState<SourceDescriptor[]>([])
  const [selectedCell, setSelectedCell] = useState<ForecastFeature | null>(null)
  const [inspectorTab, setInspectorTab] = useState<InspectorTab>('cell')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [lastRun, setLastRun] = useState<Date | null>(null)
  const [apiUrl, setApiUrl] = useState(() => getApiBaseUrl() || ULTRA_API_CANDIDATE)
  const [apiConnected, setApiConnected] = useState(false)
  const [apiChecking, setApiChecking] = useState(false)
  const [apiStatus, setApiStatus] = useState('Offline demo · no server required')
  const [desktopStatus, setDesktopStatus] = useState(isDesktop ? 'Windows desktop shell ready' : '')
  const [showConnection, setShowConnection] = useState(false)

  const stats = useMemo(() => {
    if (!data?.features.length) return null
    const values = data.features.map(f => f.properties.combined)
    const confidence = data.features.map(f => f.properties.confidence)
    const real = data.features.filter(f => !f.properties.synthetic_habitat).length
    const high = values.filter(value => value >= 0.6).length
    return {
      cells: values.length,
      real,
      high,
      max: Math.max(...values),
      mean: values.reduce((a, b) => a + b, 0) / values.length,
      confidence: confidence.reduce((a, b) => a + b, 0) / confidence.length,
    }
  }, [data])

  async function load() {
    setLoading(true)
    setError('')
    try {
      const next = await fetchCells(lat, lon, radius, species, dataMode, resolution)
      setData(next)
      setLastRun(new Date())
      setSelectedCell(current => {
        if (!current) return null
        return next.features.find(feature => feature.properties.h3 === current.properties.h3) || null
      })
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }

  async function loadSources() {
    try {
      setSources(await fetchSources())
    } catch {
      setSources([])
    }
  }

  useEffect(() => {
    void load()

    if (isDesktop && window.mykoDesktop) {
      void window.mykoDesktop.getRuntimeInfo()
        .then(info => setDesktopStatus(`Windows ${info.arch} · Electron ${info.electron} · app ${info.version}`))
        .catch(() => setDesktopStatus('Windows desktop shell ready'))
    }

    const saved = getApiBaseUrl()
    const candidate = saved || (isDesktop ? ULTRA_API_CANDIDATE : '')
    if (!candidate) {
      void loadSources()
      return
    }

    setApiChecking(true)
    setApiStatus(saved ? 'Checking saved HTTPS API…' : 'Auto-connecting desktop HTTPS API…')
    void checkApiHealth(candidate)
      .then(health => {
        const normalized = setApiBaseUrl(candidate)
        setApiUrl(normalized)
        setApiConnected(true)
        setApiStatus(`Connected · ${health.service || 'MykoKnoks'} ${health.version || ''}`.trim())
        return loadSources()
      })
      .catch(() => {
        if (saved) setApiBaseUrl('')
        setApiConnected(false)
        setApiStatus(isDesktop ? 'Desktop API unavailable · local demo ready' : 'Saved server unavailable · running offline demo')
        return loadSources()
      })
      .finally(() => setApiChecking(false))
  }, [])

  function submit(e: FormEvent) {
    e.preventDefault()
    void load()
  }

  async function connectApi() {
    setApiChecking(true)
    setError('')
    setApiStatus('Testing HTTPS API…')
    try {
      const health = await checkApiHealth(apiUrl)
      const normalized = setApiBaseUrl(apiUrl)
      setApiUrl(normalized)
      setApiConnected(true)
      setApiStatus(`Connected · ${health.service || 'MykoKnoks'} ${health.version || ''}`.trim())
      await loadSources()
    } catch (e) {
      setApiConnected(false)
      setApiStatus('Connection failed · demo remains available')
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setApiChecking(false)
    }
  }

  function useOfflineDemo() {
    setApiBaseUrl('')
    setApiConnected(false)
    setDataMode('demo')
    setApiStatus('Offline demo · no server required')
    setError('')
    void loadSources()
  }

  function useMyLocation() {
    if (!navigator.geolocation) {
      setError('Position is not available on this device.')
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
        setError(`Could not get position: ${err.message}`)
        setLoading(false)
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 30000 },
    )
  }

  function changeMode(mode: DataMode) {
    if (mode !== 'demo' && !apiConnected) {
      setError('Connect the MykoKnoks HTTPS API before Live or H3 Store is used.')
      setShowConnection(true)
      return
    }
    setError('')
    setDataMode(mode)
    setSelectedCell(null)
    if (mode === 'live') {
      setRadius(current => Math.min(current, 1))
      setResolution(9)
    }
  }

  function selectCell(feature: ForecastFeature | null) {
    setSelectedCell(feature)
    if (feature) setInspectorTab('cell')
  }

  async function exportPdf() {
    if (!window.mykoDesktop) return
    try {
      const result = await window.mykoDesktop.savePdf()
      if (result.ok) setDesktopStatus(`PDF saved · ${result.path || 'completed'}`)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  async function exportScreenshot() {
    if (!window.mykoDesktop) return
    try {
      const result = await window.mykoDesktop.saveScreenshot()
      if (result.ok) setDesktopStatus(`Screenshot saved · ${result.path || 'completed'}`)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  const activeMode = MODE_COPY[dataMode]
  const selected = selectedCell?.properties

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <div className="brand-mark" aria-hidden="true"><span>MK</span></div>
          <div>
            <div className="eyebrow">NORDIC ECOLOGICAL INTELLIGENCE</div>
            <div className="brand-line"><h1>MykoKnoks</h1><span>v{appVersion}</span></div>
          </div>
        </div>

        <div className="topbar-center">
          <button type="button" className={`status-pill ${apiConnected ? 'online' : ''}`} onClick={() => setShowConnection(value => !value)}>
            <i />
            <span>{apiConnected ? 'Ultra API online' : 'Local-first'}</span>
            <small>{dataMode.toUpperCase()}</small>
          </button>
        </div>

        <div className="topbar-actions">
          {isDesktop && <button type="button" className="icon-action" title="Save map screenshot" onClick={() => void exportScreenshot()}>Capture</button>}
          {isDesktop && <button type="button" className="icon-action primary" title="Export report as PDF" onClick={() => void exportPdf()}>Export PDF</button>}
        </div>
      </header>

      {showConnection && (
        <section className="connection-drawer">
          <div>
            <div className="section-kicker">SERVER CONNECTION</div>
            <strong>{apiStatus}</strong>
          </div>
          <label className="connection-input">
            <span>HTTPS API base URL</span>
            <input
              type="url"
              value={apiUrl}
              onChange={e => setApiUrl(e.target.value)}
              placeholder={ULTRA_API_CANDIDATE}
              autoCapitalize="none"
              autoCorrect="off"
            />
          </label>
          <button type="button" disabled={apiChecking} onClick={() => void connectApi()}>{apiChecking ? 'Testing…' : 'Test & connect'}</button>
          <button type="button" className="ghost" onClick={useOfflineDemo}>Use offline demo</button>
        </section>
      )}

      {error && <div className="global-error"><strong>Action required</strong><span>{error}</span><button type="button" onClick={() => setError('')}>×</button></div>}

      <section className="workspace">
        <aside className="control-rail glass-panel">
          <div className="rail-heading">
            <div><div className="section-kicker">FORECAST RUN</div><h2>Explore conditions</h2></div>
            <span className={`tiny-live ${apiConnected ? 'online' : ''}`}>{activeMode.short}</span>
          </div>

          <form onSubmit={submit}>
            <div className="mode-switch" aria-label="Data mode">
              {(Object.keys(MODE_COPY) as DataMode[]).map(mode => (
                <button
                  key={mode}
                  type="button"
                  disabled={mode !== 'demo' && !apiConnected}
                  className={dataMode === mode ? 'active' : ''}
                  onClick={() => changeMode(mode)}
                >
                  <span>{MODE_COPY[mode].label}</span>
                  <small>{MODE_COPY[mode].short}</small>
                </button>
              ))}
            </div>
            <p className="mode-copy">{activeMode.description}</p>

            <div className="field-block">
              <label>
                <span className="field-label">Species / taxon</span>
                <input value={species} onChange={e => setSpecies(e.target.value)} list="species-presets" />
                <datalist id="species-presets">
                  <option value="Psilocybe semilanceata" />
                  <option value="Cantharellus cibarius" />
                  <option value="Boletus edulis" />
                  <option value="Craterellus tubaeformis" />
                </datalist>
              </label>
            </div>

            <div className="field-block">
              <div className="field-title"><span>Search center</span><button type="button" className="text-button" onClick={useMyLocation}>Use my position</button></div>
              <div className="coordinate-grid">
                <label><span>Latitude</span><input type="number" step="0.0001" value={lat} onChange={e => setLat(Number(e.target.value))} /></label>
                <label><span>Longitude</span><input type="number" step="0.0001" value={lon} onChange={e => setLon(Number(e.target.value))} /></label>
              </div>
              <button type="button" className="preset-button" onClick={() => { setLat(DEFAULT_LAT); setLon(DEFAULT_LON) }}>Jæren preset · 58.735, 5.647</button>
            </div>

            <div className="field-block compact-grid">
              <label>
                <span className="field-label">H3 resolution</span>
                <select value={resolution} onChange={e => setResolution(Number(e.target.value))}>
                  <option value={8}>8 · regional</option>
                  <option value={9}>9 · local</option>
                  <option value={10}>10 · fine</option>
                </select>
              </label>
              <label>
                <span className="field-label">Radius</span>
                <div className="range-readout"><strong>{radius.toFixed(1)} km</strong><span>{dataMode === 'live' ? 'live cap' : 'search area'}</span></div>
              </label>
            </div>

            <input
              className="radius-slider"
              aria-label="Search radius"
              type="range"
              min="0.3"
              max={dataMode === 'live' ? '1.2' : '15'}
              step="0.1"
              value={radius}
              onChange={e => setRadius(Number(e.target.value))}
            />

            <button className="run-button" disabled={loading}>
              <span>{loading ? 'Running forecast…' : 'Run forecast'}</span>
              <small>{dataMode === 'demo' ? 'local compute' : 'HTTPS data pipeline'}</small>
            </button>
          </form>

          <div className="run-summary">
            <div className="section-kicker">RUN SUMMARY</div>
            <div className="summary-grid">
              <div><span>Cells</span><strong>{stats?.cells ?? '—'}</strong></div>
              <div><span>High</span><strong>{stats?.high ?? '—'}</strong></div>
              <div><span>Real</span><strong>{stats?.real ?? '—'}</strong></div>
              <div><span>Confidence</span><strong>{stats ? pct(stats.confidence) : '—'}</strong></div>
            </div>
            <div className="run-meta"><span>{lastRun ? `Updated ${lastRun.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : 'Not run yet'}</span><span>H3 r{resolution}</span></div>
          </div>
        </aside>

        <section className="map-stage glass-panel">
          <div className="map-toolbar">
            <div>
              <div className="section-kicker">MAP LAYER</div>
              <div className="metric-switch">
                {METRICS.map(item => (
                  <button key={item.id} type="button" className={metric === item.id ? 'active' : ''} onClick={() => setMetric(item.id)}>{item.label}</button>
                ))}
              </div>
            </div>
            <div className="map-run-state">
              <span className={loading ? 'pulse' : ''} />
              <div><strong>{loading ? 'Computing' : `${stats?.cells ?? 0} cells rendered`}</strong><small>{species}</small></div>
            </div>
          </div>

          <div className="map-canvas-wrap">
            <MapView
              data={data}
              center={[lon, lat]}
              metric={metric}
              selectedH3={selected?.h3 || null}
              onSelect={selectCell}
            />
            <div className="legend-card">
              <div><span>LOW</span><span>HIGH</span></div>
              <i className="legend-gradient" />
              <small>{METRICS.find(item => item.id === metric)?.label} score · 0–100%</small>
            </div>
            <div className="map-hint">Click an H3 cell to inspect evidence</div>
          </div>
        </section>

        <aside className="inspector glass-panel">
          <div className="inspector-tabs">
            <button type="button" className={inspectorTab === 'cell' ? 'active' : ''} onClick={() => setInspectorTab('cell')}>Cell</button>
            <button type="button" className={inspectorTab === 'sources' ? 'active' : ''} onClick={() => setInspectorTab('sources')}>Sources</button>
            <button type="button" className={inspectorTab === 'system' ? 'active' : ''} onClick={() => setInspectorTab('system')}>System</button>
          </div>

          {inspectorTab === 'cell' && selected && (
            <div className="inspector-content">
              <div className="cell-title">
                <div><div className="section-kicker">SELECTED H3 CELL</div><h2>{selected.species}</h2></div>
                <button type="button" className="close-cell" onClick={() => setSelectedCell(null)}>×</button>
              </div>
              <code className="h3-code">{selected.h3}</code>

              <div className="score-hero">
                <span>Combined suitability</span>
                <strong>{pct(selected.combined)}</strong>
                <small>{selected.synthetic_habitat ? 'Synthetic demo surface' : 'Evidence-backed feature cell'}</small>
              </div>

              <div className="score-stack">
                <ScoreBar label="Habitat" value={selected.habitat} />
                <ScoreBar label="Fruiting" value={selected.fruiting} />
                <ScoreBar label="Confidence" value={selected.confidence} />
              </div>

              <div className="inspector-section">
                <div className="section-kicker">ENVIRONMENT</div>
                <div className="property-grid">
                  <div><span>Elevation</span><strong>{selected.elevation_m == null ? 'n/a' : `${Math.round(selected.elevation_m)} m`}</strong></div>
                  <div><span>Terrain</span><strong>{selected.terrain || 'n/a'}</strong></div>
                  <div><span>Mode</span><strong>{selected.data_mode}</strong></div>
                  <div><span>Confidence</span><strong>{pct(selected.confidence)}</strong></div>
                </div>
              </div>

              <div className="inspector-section">
                <div className="section-kicker">DRIVERS</div>
                <div className="tag-cloud">{selected.drivers.map(driver => <span key={driver}>{driver}</span>)}</div>
              </div>

              <div className="inspector-section">
                <div className="section-kicker">PROVENANCE</div>
                <ul className="provenance-list">{selected.provenance.map(source => <li key={source}>{source}</li>)}</ul>
              </div>

              {selected.source_warnings.length > 0 && (
                <div className="warning-card"><strong>Interpretation limits</strong>{selected.source_warnings.map(warning => <p key={warning}>{warning}</p>)}</div>
              )}
            </div>
          )}

          {inspectorTab === 'cell' && !selected && (
            <div className="inspector-content empty-inspector">
              <div className="empty-orbit"><span /></div>
              <div className="section-kicker">CONTEXT INSPECTOR</div>
              <h2>Select a map cell</h2>
              <p>Inspect suitability decomposition, confidence, terrain, model drivers and provenance without leaving the map.</p>
              {stats && (
                <div className="overview-cards">
                  <div><span>Mean suitability</span><strong>{pct(stats.mean)}</strong></div>
                  <div><span>Peak suitability</span><strong>{pct(stats.max)}</strong></div>
                </div>
              )}
            </div>
          )}

          {inspectorTab === 'sources' && (
            <div className="inspector-content">
              <div className="section-kicker">DATA PIPELINE</div>
              <h2>Source health</h2>
              <p className="inspector-lead">Providers surfaced by the backend. A green indicator means the connected API reports the source as live.</p>
              <div className="source-stack">
                {sources.map(source => (
                  <div className="source-card" key={source.id}>
                    <i className={apiConnected && source.live ? 'online' : ''} />
                    <div><strong>{source.name}</strong><span>{source.organisation} · {source.kind}</span><small>{source.role}</small></div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {inspectorTab === 'system' && (
            <div className="inspector-content">
              <div className="section-kicker">RUNTIME</div>
              <h2>System status</h2>
              <div className="system-card"><span>Desktop runtime</span><strong>{isDesktop ? desktopStatus : 'Web / Android runtime'}</strong></div>
              <div className="system-card"><span>Backend</span><strong>{apiStatus}</strong></div>
              <div className="system-card"><span>API endpoint</span><code>{apiUrl || 'not configured'}</code></div>
              <button type="button" className="wide-secondary" onClick={() => setShowConnection(true)}>Connection settings</button>
              <div className="science-card">
                <div className="section-kicker">SCIENTIFIC GUARDRAIL</div>
                <strong>Suitability is not confirmed presence.</strong>
                <p>Scores are ecological decision support, not species identification, edibility advice or a validated occurrence probability. Demo cells are explicitly synthetic.</p>
              </div>
            </div>
          )}
        </aside>
      </section>

      <footer className="statusbar">
        <div><i className={apiConnected ? 'online' : ''} /><span>{apiConnected ? 'Secure HTTPS backend connected' : 'Offline-capable local runtime'}</span></div>
        <div><span>{desktopStatus || `MykoKnoks ${appVersion}`}</span><span>•</span><span>{dataMode.toUpperCase()}</span><span>•</span><span>{metric.toUpperCase()}</span></div>
      </footer>
    </main>
  )
}
