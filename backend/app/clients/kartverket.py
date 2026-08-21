from __future__ import annotations

from xml.etree import ElementTree

import httpx

from app.schemas import TerrainSnapshot


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_elevation_response(xml_text: str) -> TerrainSnapshot:
    """Parse Kartverket WPS output without depending on exact namespace prefixes."""
    root = ElementTree.fromstring(xml_text)
    outputs: dict[str, str] = {}

    for output in root.iter():
        if _local_name(output.tag) != "Output":
            continue
        identifier = None
        value = None
        for node in output.iter():
            name = _local_name(node.tag)
            text = (node.text or "").strip()
            if name == "Identifier" and text and identifier is None:
                identifier = text
            elif name in {"LiteralData", "ComplexData"} and text:
                value = text
        if identifier and value is not None:
            outputs[identifier.lower()] = value

    if not outputs:
        literals = [
            (node.text or "").strip()
            for node in root.iter()
            if _local_name(node.tag) == "LiteralData" and (node.text or "").strip()
        ]
        if literals:
            outputs["elevation"] = literals[0]

    elevation = None
    for key in ("elevation", "height", "hoyde", "høgde"):
        if key in outputs:
            try:
                elevation = float(outputs[key].replace(",", "."))
            except ValueError:
                elevation = None
            break

    terrain = outputs.get("terrain") or outputs.get("terreng")
    placenames = [
        value
        for key, value in outputs.items()
        if key.startswith("placename") or key in {"name", "stedsnavn"}
    ]
    return TerrainSnapshot(elevation_m=elevation, terrain=terrain, placenames=placenames)


class KartverketElevationClient:
    def __init__(self, base_url: str, timeout_seconds: float = 20.0) -> None:
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds

    async def point(self, lat: float, lon: float) -> TerrainSnapshot:
        params = {
            "request": "Execute",
            "service": "WPS",
            "version": "1.0.0",
            "identifier": "elevation",
            "datainputs": f"lat={lat};lon={lon};epsg=4326",
        }
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
        return parse_elevation_response(response.text)
