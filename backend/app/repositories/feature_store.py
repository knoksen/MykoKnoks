from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import bindparam, create_engine, text
from sqlalchemy.engine import Engine

from app.scoring import HabitatFeatures


@dataclass(frozen=True)
class StoredEnvironmentalFeatures:
    h3: str
    habitat: HabitatFeatures
    completeness: float
    provenance: list[str]
    terrain: str | None = None


class FeatureStoreRepository:
    """Read normalized H3 environmental features from PostgreSQL or SQLite.

    Serving only needs scalar features keyed by H3. Geometry is reconstructed from the
    H3 index by the API, so the lightweight Ultra store does not require PostGIS.
    """

    def __init__(self, database_url: str, engine: Engine | None = None) -> None:
        self.engine = engine or create_engine(database_url, pool_pre_ping=True)

    @property
    def provenance_name(self) -> str:
        if self.engine.dialect.name == "sqlite":
            return "sqlite_h3_env_features"
        if self.engine.dialect.name == "postgresql":
            return "postgres_h3_env_features"
        return f"{self.engine.dialect.name}_h3_env_features"

    def get_many(self, cells: list[str]) -> dict[str, StoredEnvironmentalFeatures]:
        if not cells:
            return {}

        query = text(
            """
            SELECT
              h3,
              elevation_m,
              terrain,
              grassland_proxy,
              forest_edge_proxy,
              soil_moisture_proxy,
              completeness
            FROM env_features
            WHERE h3 IN :cells
            """
        ).bindparams(bindparam("cells", expanding=True))

        with self.engine.connect() as conn:
            rows = conn.execute(query, {"cells": cells}).mappings().all()

        result: dict[str, StoredEnvironmentalFeatures] = {}
        for row in rows:
            result[row["h3"]] = StoredEnvironmentalFeatures(
                h3=row["h3"],
                habitat=HabitatFeatures(
                    grassland=float(0.5 if row["grassland_proxy"] is None else row["grassland_proxy"]),
                    forest_edge=float(0.5 if row["forest_edge_proxy"] is None else row["forest_edge_proxy"]),
                    soil_moisture_proxy=float(
                        0.5 if row["soil_moisture_proxy"] is None else row["soil_moisture_proxy"]
                    ),
                    elevation_m=float(150.0 if row["elevation_m"] is None else row["elevation_m"]),
                ),
                completeness=float(0.0 if row["completeness"] is None else row["completeness"]),
                provenance=[self.provenance_name],
                terrain=row["terrain"],
            )
        return result
