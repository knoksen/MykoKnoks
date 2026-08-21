from pydantic import BaseModel, Field


class WeatherSnapshot(BaseModel):
    air_temperature_c: float | None = None
    relative_humidity_pct: float | None = None
    precipitation_1h_mm: float | None = None
    wind_speed_mps: float | None = None
    source: str
    time: str | None = None


class ScoreBreakdown(BaseModel):
    habitat: float = Field(ge=0, le=1)
    fruiting: float = Field(ge=0, le=1)
    combined: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    drivers: list[str]
