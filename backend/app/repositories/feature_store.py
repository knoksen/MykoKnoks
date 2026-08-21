from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import create_engine, text
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
    def __init__(self, database_url: str, engine: Engine | None = None) -> None:
        self.engine = engine or create_engine(database_url, pool_pre_ping=True)

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
            WHERE h3 = ANY(:cells)
            """
        )
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
                provenance=["postgis_env_features"],
                terrain=row["terrain"],
            )
        return result
