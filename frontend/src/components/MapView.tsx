import { useEffect,useRef } from 'react'
import maplibregl,{Map} from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import type {ForecastCollection} from '../api'

type Props={data:ForecastCollection|null;center:[number,number]}
const SOURCE='forecast-cells'
export default function MapView({data,center}:Props){const container=useRef<HTMLDivElement|null>(null);const mapRef=useRef<Map|null>(null)
useEffect(()=>{if(!container.current||mapRef.current)return;const map=new maplibregl.Map({container:container.current,style:'https://demotiles.maplibre.org/style.json',center,zoom:9.8});map.addControl(new maplibregl.NavigationControl(),'top-right');map.on('load',()=>{map.addSource(SOURCE,{type:'geojson',data:data||{type:'FeatureCollection',features:[]}});map.addLayer({id:'forecast-fill',type:'fill',source:SOURCE,paint:{'fill-color':['interpolate',['linear'],['get','combined'],0,'#25332d',0.25,'#7c6f3e',0.5,'#8e9a45',0.75,'#4fa85d',1,'#33d17a'],'fill-opacity':0.68,'fill-outline-color':'#d8f3dc'}});map.on('click','forecast-fill',event=>{const feature=event.features?.[0];if(!feature)return;const p=feature.properties as Record<string,unknown>;new maplibregl.Popup().setLngLat(event.lngLat).setHTML(`<strong>${String(p.species)}</strong><br/>Combined: ${Number(p.combined).toFixed(2)}<br/>Habitat: ${Number(p.habitat).toFixed(2)}<br/>Fruiting: ${Number(p.fruiting).toFixed(2)}<br/>Confidence: ${Number(p.confidence).toFixed(2)}`).addTo(map)})});mapRef.current=map;return()=>{map.remove();mapRef.current=null}},[])
useEffect(()=>{const map=mapRef.current;if(!map||!data)return;const update=()=>{const source=map.getSource(SOURCE) as maplibregl.GeoJSONSource|undefined;source?.setData(data as never);map.easeTo({center,duration:500})};if(map.isStyleLoaded())update();else map.once('load',update)},[data,center]);return <div ref={container} className="map"/>}
