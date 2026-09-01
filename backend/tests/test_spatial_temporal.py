import h3
import pytest

from app.services.spatial_temporal import SpatialTemporalService, select_weather_nodes


def _payload(temp: float) -> dict:
    return {
        "properties": {
            "timeseries": [
                {
                    "time": "2026-09-01T09:00:00Z",
                    "data": {
                        "instant": {
                            "details": {
                                "air_temperature": temp,
                                "relative_humidity": 88.0,
                                "wind_speed": 3.0,
                            }
                        },
                        "next_1_hours": {"details": {"precipitation_amount": 0.4}},
                    },
                }
            ]
        }
    }


class FakeMetClient:
    def __init__(self) -> None:
        self.calls: list[tuple[float, float]] = []

    async def raw_forecast(self, lat: float, lon: float) -> dict:
        self.calls.append((lat, lon))
        return _payload(8.0 + (lon % 1.0) * 10.0)


def _cells() -> list[str]:
    origin = h3.latlng_to_cell(58.735, 5.647, 9)
    return sorted(h3.grid_disk(origin, 2))


def test_weather_node_selection_is_deterministic_and_bounded() -> None:
    cells = _cells()
    first = select_weather_nodes(cells, 5)
    second = select_weather_nodes(list(reversed(cells)), 5)

    assert first == second
    assert len(first) == 5
    assert len(set(first)) == 5
    assert set(first) <= set(cells)


@pytest.mark.asyncio
async def test_spatial_weather_assigns_cells_and_reuses_cache() -> None:
    client = FakeMetClient()
    service = SpatialTemporalService(
        client,
        cache_ttl_seconds=300,
        max_nodes=4,
        concurrency=2,
    )
    cells = _cells()

    first = await service.forecast_cells(cells, days=2)

    assert len(first["weather_nodes"]) == 4
    assert len(first["cells"]) == len(cells)
    assert first["data_quality"]["weather_node_coverage_ratio"] == 1.0
    assert first["data_quality"]["label"] in {"high", "moderate", "limited"}
    assert len(client.calls) == 4
    assert all(item["weather_node_distance_km"] >= 0 for item in first["cells"])
    assert all(node["forecast"]["days"] for node in first["weather_nodes"])

    second = await service.forecast_cells(cells, days=2)

    assert len(client.calls) == 4
    assert all(node["cached"] is True for node in second["weather_nodes"])
