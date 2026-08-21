from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "MykoKnoks"
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:5173"
    database_url: str = "postgresql+psycopg://mykoknoks:mykoknoks@localhost:5432/mykoknoks"
    met_user_agent: str = "MykoKnoks/0.1 https://github.com/knoksen/MykoKnoks"
    met_timeout_seconds: float = 10.0
    default_h3_resolution: int = 9
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
