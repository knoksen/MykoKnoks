from app.clients.ogc import lonlat_to_web_mercator, parse_wms_layers

CAPABILITIES = """<WMS_Capabilities xmlns='http://www.opengis.net/wms'>
<Capability><Layer><Title>Root</Title>
  <Layer queryable='1'><Name>ar5_arealtype</Name><Title>AR5 arealtype</Title></Layer>
  <Layer><Name>background</Name><Title>Background</Title></Layer>
</Layer></Capability></WMS_Capabilities>"""


def test_parse_wms_layers():
    layers = parse_wms_layers(CAPABILITIES)
    assert layers[0].name == "ar5_arealtype"
    assert layers[0].queryable is True
    assert layers[1].queryable is False


def test_web_mercator_zero():
    x, y = lonlat_to_web_mercator(0.0, 0.0)
    assert abs(x) < 1e-6
    assert abs(y) < 1e-6
