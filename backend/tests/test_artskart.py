from app.clients.artskart import web_mercator_bbox_wkt


def test_bbox_wkt_is_closed_polygon():
    wkt = web_mercator_bbox_wkt(58.735, 5.647, 1000)
    assert wkt.startswith("POLYGON((")
    assert wkt.endswith("))")
    coords = wkt.removeprefix("POLYGON((").removesuffix("))").split(",")
    assert len(coords) == 5
    assert coords[0] == coords[-1]
