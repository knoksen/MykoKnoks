export type ForecastProperties={h3:string;species:string;habitat:number;fruiting:number;combined:number;confidence:number;drivers:string[];synthetic_habitat:boolean}
export type ForecastFeature={type:'Feature';id?:string;geometry:{type:'Polygon';coordinates:number[][][]};properties:ForecastProperties}
export type ForecastCollection={type:'FeatureCollection';features:ForecastFeature[];metadata?:Record<string,unknown>}
const BASE=import.meta.env.VITE_API_BASE_URL||'http://localhost:8000'
export async function fetchCells(lat:number,lon:number,radiusKm:number,species:string):Promise<ForecastCollection>{const params=new URLSearchParams({lat:String(lat),lon:String(lon),radius_km:String(radiusKm),species});const response=await fetch(`${BASE}/api/v1/cells?${params}`);if(!response.ok)throw new Error(`API error ${response.status}`);return response.json()}
