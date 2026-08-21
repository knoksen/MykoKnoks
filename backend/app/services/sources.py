from app.config import Settings
from app.schemas import SourceDescriptor


def source_catalog(settings: Settings) -> list[SourceDescriptor]:
    return [
        SourceDescriptor(
            id="met_locationforecast",
            name="Locationforecast 2.0",
            organisation="MET Norway",
            kind="forecast-api",
            endpoint="https://api.met.no/weatherapi/locationforecast/2.0/compact",
            role="Short-range weather and fruiting features",
            license="MET Norway terms / attribution",
        ),
        SourceDescriptor(
            id="artskart",
            name="Artskart public API",
            organisation="Artsdatabanken",
            kind="occurrence-api",
            endpoint="https://artskart.artsdatabanken.no/publicapi/api",
            role="Species occurrences and taxonomy",
        ),
        SourceDescriptor(
            id="kartverket_elevation",
            name="Elevation WPS",
            organisation="Kartverket / Geonorge",
            kind="ogc-wps",
            endpoint=settings.kartverket_elevation_url,
            role="Elevation and terrain evidence",
            license="NLOD / Kartverket terms",
        ),
        SourceDescriptor(
            id="nibio_ar5",
            name="AR5",
            organisation="NIBIO",
            kind="ogc-wms",
            endpoint=settings.nibio_ar5_wms_url,
            role="Land-resource / land-cover evidence",
            license="NLOD where applicable",
        ),
        SourceDescriptor(
            id="nibio_sr16",
            name="SR16 forest resource map",
            organisation="NIBIO",
            kind="ogc-wms",
            endpoint=settings.nibio_sr16_wms_url,
            role="Forest structure and tree-species evidence",
            license="NLOD where applicable",
        ),
        SourceDescriptor(
            id="ngu_losmasse",
            name="Løsmasser",
            organisation="NGU",
            kind="ogc-wms",
            endpoint=settings.ngu_losmasse_wms_url,
            role="Quaternary geology and loose-sediment evidence",
            license="NLOD; attribute NGU",
        ),
        SourceDescriptor(
            id="copernicus_s2",
            name="Sentinel-2 L2A",
            organisation="Copernicus Data Space Ecosystem",
            kind="stac",
            endpoint="https://stac.dataspace.copernicus.eu/v1/search",
            role="Vegetation indices and seasonal surface state",
            license="Copernicus data terms",
        ),
    ]
