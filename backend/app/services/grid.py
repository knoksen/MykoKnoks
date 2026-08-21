from __future__ import annotations

import hashlib

from app.scoring import HabitatFeatures


def _stable_unit(value: str, salt: str) -> float:
    digest = hashlib.blake2b(f"{salt}:{value}".encode(), digest_size=8).digest()
    integer = int.from_bytes(digest, "big")
    return integer / float(2**64 - 1)


def synthetic_habitat_features(cell: str) -> HabitatFeatures:
    return HabitatFeatures(
        grassland=_stable_unit(cell, "grassland"),
        forest_edge=_stable_unit(cell, "edge"),
        soil_moisture_proxy=_stable_unit(cell, "moisture"),
        elevation_m=20.0 + 650.0 * _stable_unit(cell, "elevation"),
    )


def _h3():
    import h3
    return h3


def cells_around(lat: float, lon: float, radius_km: float, resolution: int) -> list[str]:
    h3 = _h3()
    origin = h3.latlng_to_cell(lat, lon, resolution)
    edge_km = max(0.001, h3.average_hexagon_edge_length(resolution, unit="km"))
    rings = max(1, min(25, int(radius_km / (edge_km * 1.6)) + 1))
    return list(h3.grid_disk(origin, rings))


def cell_geometry(cell: str) -> dict:
    h3 = _h3()
    boundary = h3.cell_to_boundary(cell)
    coordinates = [[lon, lat] for lat, lon in boundary]
    coordinates.append(coordinates[0])
    return {"type": "Polygon", "coordinates": [coordinates]}
