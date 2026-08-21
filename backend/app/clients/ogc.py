from __future__ import annotations

from dataclasses import dataclass
from math import log, pi, radians, tan
from xml.etree import ElementTree

import httpx

from app.schemas import WmsLayer


@dataclass(frozen=True)
class FeatureInfoResult:
    source: str
    layer: str
    payload: dict | str | None
    content_type: str | None = None


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_wms_layers(xml_text: str) -> list[WmsLayer]:
    root = ElementTree.fromstring(xml_text)
    layers: list[WmsLayer] = []
    for node in root.iter():
        if _local_name(node.tag) != "Layer":
            continue
        name = None
        title = None
        for child in list(node):
            local = _local_name(child.tag)
            if local == "Name":
                name = (child.text or "").strip()
            elif local == "Title":
                title = (child.text or "").strip()
        if name:
            layers.append(
                WmsLayer(
                    name=name,
                    title=title or name,
                    queryable=node.attrib.get("queryable", "0") in {"1", "true", "TRUE"},
                )
            )
    return layers


def lonlat_to_web_mercator(lon: float, lat: float) -> tuple[float, float]:
    x = lon * 20037508.34 / 180.0
    clamped_lat = max(-85.05112878, min(85.05112878, lat))
    y = log(tan((90.0 + clamped_lat) * pi / 360.0)) / radians(1.0)
    y = y * 20037508.34 / 180.0
    return x, y


class WmsClient:
    def __init__(self, base_url: str, source_id: str, timeout_seconds: float = 20.0) -> None:
        self.base_url = base_url
        self.source_id = source_id
        self.timeout_seconds = timeout_seconds
        self._layers: list[WmsLayer] | None = None

    async def capabilities(self, refresh: bool = False) -> list[WmsLayer]:
        if self._layers is not None and not refresh:
            return self._layers
        params = {"SERVICE": "WMS", "REQUEST": "GetCapabilities", "VERSION": "1.3.0"}
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
        self._layers = parse_wms_layers(response.text)
        return self._layers

    async def find_layer(self, terms: tuple[str, ...]) -> WmsLayer | None:
        layers = await self.capabilities()
        lowered = tuple(term.casefold() for term in terms)
        candidates = [layer for layer in layers if layer.queryable] or layers
        for layer in candidates:
            haystack = f"{layer.name} {layer.title}".casefold()
            if any(term in haystack for term in lowered):
                return layer
        return candidates[0] if candidates else None

    async def feature_info(
        self,
        lat: float,
        lon: float,
        layer_name: str,
        radius_m: float = 40.0,
    ) -> FeatureInfoResult:
        x, y = lonlat_to_web_mercator(lon, lat)
        bbox = f"{x-radius_m},{y-radius_m},{x+radius_m},{y+radius_m}"
        params = {
            "SERVICE": "WMS",
            "VERSION": "1.3.0",
            "REQUEST": "GetFeatureInfo",
            "LAYERS": layer_name,
            "QUERY_LAYERS": layer_name,
            "CRS": "EPSG:3857",
            "BBOX": bbox,
            "WIDTH": "101",
            "HEIGHT": "101",
            "I": "50",
            "J": "50",
            "FEATURE_COUNT": "5",
            "INFO_FORMAT": "application/json",
        }
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(self.base_url, params=params)
            if response.status_code >= 400:
                params["INFO_FORMAT"] = "text/plain"
                response = await client.get(self.base_url, params=params)
            response.raise_for_status()

        content_type = response.headers.get("content-type")
        payload: dict | str | None
        try:
            payload = response.json()
        except ValueError:
            payload = response.text[:12000] if response.text else None
        return FeatureInfoResult(
            source=self.source_id,
            layer=layer_name,
            payload=payload,
            content_type=content_type,
        )
