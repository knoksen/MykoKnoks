export type GISLayerGroup = 'landcover' | 'forest' | 'geology' | 'terrain' | 'ecology' | 'species' | 'imagery'

export type GISLayerDefinition = {
  id: string
  group: GISLayerGroup
  label: string
  short: string
  provider: string
  description: string
  endpoint?: string
  wmsLayer?: string
  legendLayer?: string
  defaultOpacity: number
  defaultVisible?: boolean
  queryable?: boolean
  minZoom?: number
  maxZoom?: number
  restricted?: boolean
  sourceUrl: string
}

export type GISLayerRuntimeState = {
  visible: boolean
  opacity: number
}

export type GISIdentifyResult = {
  layerId: string
  label: string
  provider: string
  ok: boolean
  status: number
  body: string
}

export const GIS_GROUP_LABELS: Record<GISLayerGroup, string> = {
  landcover: 'Land cover',
  forest: 'Forest',
  geology: 'Geology',
  terrain: 'Terrain',
  ecology: 'Ecology',
  species: 'Species',
  imagery: 'Imagery',
}

export const GIS_LAYERS: GISLayerDefinition[] = [
  {
    id: 'ar5-arealtype',
    group: 'landcover',
    label: 'AR5 Arealtype',
    short: 'AR5',
    provider: 'NIBIO',
    description: 'Detailed land-resource classes including forest, agricultural land, open land, mire and built areas.',
    endpoint: 'https://wms.nibio.no/cgi-bin/ar5',
    wmsLayer: 'Arealtype',
    defaultOpacity: 0.58,
    queryable: true,
    minZoom: 8,
    sourceUrl: 'https://wms.nibio.no/cgi-bin/ar5?request=getcapabilities&service=wms',
  },
  {
    id: 'sr16-treslag',
    group: 'forest',
    label: 'SR16 Treslag',
    short: 'TREES',
    provider: 'NIBIO',
    description: 'National forest-resource mapping with dominant tree-species information derived from remote sensing and inventory data.',
    endpoint: 'https://wms.nibio.no/cgi-bin/sr16',
    wmsLayer: 'SRVTRESLAG',
    defaultOpacity: 0.54,
    queryable: true,
    minZoom: 7,
    sourceUrl: 'https://wms.nibio.no/cgi-bin/sr16?request=getcapabilities&service=wms',
  },
  {
    id: 'sr16-height',
    group: 'forest',
    label: 'SR16 Skoghøyde',
    short: 'HEIGHT',
    provider: 'NIBIO',
    description: 'SR16 thematic forest-height layer for structural habitat context.',
    endpoint: 'https://wms.nibio.no/cgi-bin/sr16',
    wmsLayer: 'SRVHOYDE',
    defaultOpacity: 0.48,
    queryable: true,
    minZoom: 7,
    sourceUrl: 'https://wms.nibio.no/cgi-bin/sr16?request=getcapabilities&service=wms',
  },
  {
    id: 'ngu-deposits',
    group: 'geology',
    label: 'NGU Løsmasser',
    short: 'SOIL',
    provider: 'NGU',
    description: 'Quaternary deposits and superficial geology, harmonised across available detailed, local and regional mapping.',
    endpoint: 'https://geo.ngu.no/mapserver/LosmasserWMS3',
    wmsLayer: 'Losmasser_temakart_sammenstilt',
    defaultOpacity: 0.52,
    queryable: true,
    minZoom: 5,
    sourceUrl: 'https://geo.ngu.no/mapserver/LosmasserWMS3?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities',
  },
  {
    id: 'dtm-hillshade',
    group: 'terrain',
    label: 'DTM Skyggerelieff',
    short: 'RELIEF',
    provider: 'Kartverket',
    description: 'Hillshade from the national elevation-data WMS for terrain-form interpretation.',
    endpoint: 'https://wms.geonorge.no/skwms1/wms.hoyde-dtm',
    wmsLayer: 'DTM:skyggerelieff',
    defaultOpacity: 0.42,
    queryable: false,
    minZoom: 7,
    sourceUrl: 'https://wms.geonorge.no/skwms1/wms.hoyde-dtm?request=GetCapabilities&service=WMS',
  },
  {
    id: 'dtm-slope',
    group: 'terrain',
    label: 'DTM Helning',
    short: 'SLOPE',
    provider: 'Kartverket',
    description: 'Terrain slope in degrees from the national elevation-data WMS.',
    endpoint: 'https://wms.geonorge.no/skwms1/wms.hoyde-dtm',
    wmsLayer: 'DTM:helning_grader',
    defaultOpacity: 0.48,
    queryable: false,
    minZoom: 7,
    sourceUrl: 'https://wms.geonorge.no/skwms1/wms.hoyde-dtm?request=GetCapabilities&service=WMS',
  },
  {
    id: 'ecosystems',
    group: 'ecology',
    label: 'Økosystem / våtmark',
    short: 'ECO',
    provider: 'Miljødirektoratet',
    description: 'National main-ecosystem map. Wetland is one of the mapped ecosystem classes and can be inspected at a clicked location.',
    endpoint: 'https://kart2.miljodirektoratet.no/arcgis/services/hovedokosystem/hovedokosystem/MapServer/WMSServer',
    wmsLayer: 'Hovedokosystem_detalj',
    defaultOpacity: 0.46,
    queryable: true,
    minZoom: 6,
    sourceUrl: 'https://kart2.miljodirektoratet.no/arcgis/services/hovedokosystem/hovedokosystem/MapServer/WMSServer?request=GetCapabilities&service=WMS',
  },
  {
    id: 'artskart-redlist',
    group: 'species',
    label: 'Artskart rødlista',
    short: 'SPECIES',
    provider: 'Artsdatabanken',
    description: 'Nightly WMS publication of red-listed species records with the source service precision rules.',
    endpoint: 'https://kart.artsdatabanken.no/WMS/artskart.aspx',
    wmsLayer: 'Artskart',
    defaultOpacity: 0.78,
    queryable: true,
    minZoom: 7,
    sourceUrl: 'https://kart.artsdatabanken.no/WMS/artskart.aspx?version=1.3.0&service=WMS&REQUEST=GetCapabilities',
  },
  {
    id: 'nib-ortho',
    group: 'imagery',
    label: 'Norge i bilder',
    short: 'ORTHO',
    provider: 'Kartverket / Norge i bilder',
    description: 'Orthophoto imagery. The 2026 services require a time-limited GeoID/Norge digitalt token, so no credential is embedded in MykoKnoks.',
    defaultOpacity: 0.9,
    restricted: true,
    sourceUrl: 'https://www.geonorge.no/nib',
  },
]

export function initialGISState(): Record<string, GISLayerRuntimeState> {
  return Object.fromEntries(
    GIS_LAYERS.map(layer => [
      layer.id,
      { visible: Boolean(layer.defaultVisible), opacity: layer.defaultOpacity },
    ]),
  )
}

export function wmsTileUrl(layer: GISLayerDefinition) {
  if (!layer.endpoint || !layer.wmsLayer) return null
  const params = new URLSearchParams({
    SERVICE: 'WMS',
    VERSION: '1.1.1',
    REQUEST: 'GetMap',
    LAYERS: layer.wmsLayer,
    STYLES: '',
    FORMAT: 'image/png',
    TRANSPARENT: 'true',
    SRS: 'EPSG:3857',
    WIDTH: '256',
    HEIGHT: '256',
  })
  return `${layer.endpoint}?${params.toString()}&BBOX={bbox-epsg-3857}`
}

export function wmsLegendUrl(layer: GISLayerDefinition) {
  if (!layer.endpoint || !layer.wmsLayer) return null
  const params = new URLSearchParams({
    SERVICE: 'WMS',
    VERSION: '1.1.1',
    REQUEST: 'GetLegendGraphic',
    LAYER: layer.legendLayer || layer.wmsLayer,
    FORMAT: 'image/png',
  })
  return `${layer.endpoint}?${params.toString()}`
}

function mercatorMeters(lng: number, lat: number): [number, number] {
  const radius = 6378137
  const x = radius * lng * Math.PI / 180
  const safeLat = Math.max(-85.05112878, Math.min(85.05112878, lat))
  const y = radius * Math.log(Math.tan(Math.PI / 4 + safeLat * Math.PI / 360))
  return [x, y]
}

async function fetchText(url: string) {
  if (window.mykoDesktop?.isDesktop) {
    const response = await window.mykoDesktop.httpRequest(url)
    return { ok: response.ok, status: response.status, body: response.body }
  }
  const response = await fetch(url)
  return { ok: response.ok, status: response.status, body: await response.text() }
}

export async function identifyWmsLayer(
  layer: GISLayerDefinition,
  options: {
    lng: number
    lat: number
    west: number
    south: number
    east: number
    north: number
    width: number
    height: number
    x: number
    y: number
  },
): Promise<GISIdentifyResult> {
  if (!layer.endpoint || !layer.wmsLayer || !layer.queryable) {
    return { layerId: layer.id, label: layer.label, provider: layer.provider, ok: false, status: 0, body: 'Layer is not queryable.' }
  }

  const [minX, minY] = mercatorMeters(options.west, options.south)
  const [maxX, maxY] = mercatorMeters(options.east, options.north)
  const params = new URLSearchParams({
    SERVICE: 'WMS',
    VERSION: '1.1.1',
    REQUEST: 'GetFeatureInfo',
    LAYERS: layer.wmsLayer,
    QUERY_LAYERS: layer.wmsLayer,
    STYLES: '',
    SRS: 'EPSG:3857',
    BBOX: `${minX},${minY},${maxX},${maxY}`,
    WIDTH: String(Math.max(1, Math.round(options.width))),
    HEIGHT: String(Math.max(1, Math.round(options.height))),
    X: String(Math.max(0, Math.round(options.x))),
    Y: String(Math.max(0, Math.round(options.y))),
    INFO_FORMAT: 'text/plain',
    FEATURE_COUNT: '8',
  })

  try {
    const response = await fetchText(`${layer.endpoint}?${params.toString()}`)
    return {
      layerId: layer.id,
      label: layer.label,
      provider: layer.provider,
      ok: response.ok,
      status: response.status,
      body: response.body.trim().slice(0, 2400) || 'No feature information returned at this location.',
    }
  } catch (error) {
    return {
      layerId: layer.id,
      label: layer.label,
      provider: layer.provider,
      ok: false,
      status: 0,
      body: error instanceof Error ? error.message : String(error),
    }
  }
}
