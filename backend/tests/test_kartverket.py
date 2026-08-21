from app.clients.kartverket import parse_elevation_response

SAMPLE = """<?xml version='1.0'?>
<wps:ExecuteResponse xmlns:wps='http://www.opengis.net/wps/1.0.0'
                     xmlns:ows='http://www.opengis.net/ows/1.1'>
  <wps:ProcessOutputs>
    <wps:Output><ows:Identifier>elevation</ows:Identifier><wps:Data><wps:LiteralData>42.5</wps:LiteralData></wps:Data></wps:Output>
    <wps:Output><ows:Identifier>terrain</ows:Identifier><wps:Data><wps:LiteralData>Dyrka mark</wps:LiteralData></wps:Data></wps:Output>
    <wps:Output><ows:Identifier>placename1</ows:Identifier><wps:Data><wps:LiteralData>Bryne</wps:LiteralData></wps:Data></wps:Output>
  </wps:ProcessOutputs>
</wps:ExecuteResponse>"""


def test_parse_elevation_response():
    result = parse_elevation_response(SAMPLE)
    assert result.elevation_m == 42.5
    assert result.terrain == "Dyrka mark"
    assert result.placenames == ["Bryne"]
