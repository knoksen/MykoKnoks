from app.services.weather_memory import enrich_precipitation_memory


def test_memory_accumulates_and_decays() -> None:
    points = [
        {"time": "2026-08-23T00:00:00Z", "precipitation_mm": 6.0},
        {"time": "2026-08-24T00:00:00Z", "precipitation_mm": 0.0},
        {"time": "2026-08-25T00:00:00Z", "precipitation_mm": 0.0},
    ]

    result = enrich_precipitation_memory(points, half_life_hours=48.0)

    assert result[0]["rain_memory_mm"] == 6.0
    assert 4.1 < result[1]["rain_memory_mm"] < 4.3
    assert 2.9 < result[2]["rain_memory_mm"] < 3.1
    assert result[2]["antecedent_precip_72h_mm"] == 6.0
    assert result[2]["memory_coverage_hours"] == 48.0


def test_memory_rejects_invalid_half_life() -> None:
    try:
        enrich_precipitation_memory([], half_life_hours=0)
    except ValueError as exc:
        assert "half_life_hours" in str(exc)
    else:
        raise AssertionError("expected ValueError")
