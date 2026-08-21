from sqlalchemy import create_engine, text

from app.repositories.feature_store import FeatureStoreRepository


def test_feature_store_reads_sqlite_h3_rows():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE env_features (
                    h3 TEXT PRIMARY KEY,
                    elevation_m REAL,
                    terrain TEXT,
                    grassland_proxy REAL,
                    forest_edge_proxy REAL,
                    soil_moisture_proxy REAL,
                    completeness REAL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO env_features (
                    h3, elevation_m, terrain, grassland_proxy,
                    forest_edge_proxy, soil_moisture_proxy, completeness
                ) VALUES (
                    '891f1d48967ffff', 42.5, 'gentle slope', 0.8, 0.3, 0.7, 0.9
                )
                """
            )
        )

    repo = FeatureStoreRepository("sqlite+pysqlite:///:memory:", engine=engine)
    rows = repo.get_many(["891f1d48967ffff", "missing-cell"])

    assert list(rows) == ["891f1d48967ffff"]
    stored = rows["891f1d48967ffff"]
    assert stored.habitat.elevation_m == 42.5
    assert stored.habitat.grassland == 0.8
    assert stored.habitat.forest_edge == 0.3
    assert stored.habitat.soil_moisture_proxy == 0.7
    assert stored.completeness == 0.9
    assert stored.terrain == "gentle slope"
    assert stored.provenance == ["sqlite_h3_env_features"]


def test_feature_store_empty_request_does_not_query_database():
    repo = FeatureStoreRepository("sqlite+pysqlite:///:memory:")
    assert repo.get_many([]) == {}
