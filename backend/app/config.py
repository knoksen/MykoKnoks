from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "MykoKnoks"
    app_version: str = "0.9.0"
    api_prefix: str = "/api/v1"
    root_path: str = ""
    cors_origins: str = "http://localhost:5173"
    database_url: str = "postgresql+psycopg://mykoknoks:mykoknoks@localhost:5432/mykoknoks"

    met_user_agent: str = "MykoKnoks/0.9.0 https://github.com/knoksen/MykoKnoks"
    met_timeout_seconds: float = 10.0
    upstream_timeout_seconds: float = 20.0

    default_h3_resolution: int = 9
    live_cell_limit: int = 36
    live_feature_concurrency: int = 8

    kartverket_elevation_url: str = "https://wps.geonorge.no/skwms1/wps.elevation2"
    nibio_ar5_wms_url: str = "https://wms.nibio.no/cgi-bin/ar5"
    nibio_sr16_wms_url: str = "https://wms.nibio.no/cgi-bin/sr16"
    ngu_losmasse_wms_url: str = "https://geo.ngu.no/mapserver/LosmasserWMS3"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
