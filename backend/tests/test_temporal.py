from app.services.temporal import build_temporal_forecast


def _series(time: str, temp: float, humidity: float, rain: float, hours: int = 1) -> dict:
    period = f"next_{hours}_hours"
    return {
        "time": time,
        "data": {
            "instant": {
                "details": {
                    "air_temperature": temp,
                    "relative_humidity": humidity,
                    "wind_speed": 4.0,
                }
            },
            period: {"details": {"precipitation_amount": rain}},
        },
    }


def test_temporal_forecast_groups_days_and_ranks_best_day() -> None:
    payload = {
        "properties": {
            "timeseries": [
                _series("2026-08-22T12:00:00Z", 18.0, 55.0, 0.0),
                _series("2026-08-22T18:00:00Z", 15.0, 65.0, 0.0),
                _series("2026-08-23T06:00:00Z", 11.0, 92.0, 2.0),
                _series("2026-08-23T12:00:00Z", 12.0, 88.0, 1.5),
            ]
        }
    }

    result = build_temporal_forecast(payload, days=3)

    assert len(result["points"]) == 4
    assert len(result["days"]) == 2
    assert result["best_day"]["date"] == "2026-08-23"
    assert result["best_day"]["peak_fruiting_score"] > result["days"][0]["peak_fruiting_score"]
    assert result["model"] == "weather-driven fruiting heuristic"


def test_six_hour_precipitation_is_normalised_for_scoring() -> None:
    payload = {
        "properties": {
            "timeseries": [
                _series("2026-08-22T12:00:00Z", 11.0, 90.0, 6.0, hours=6),
            ]
        }
    }

    result = build_temporal_forecast(payload, days=1)
    point = result["points"][0]

    assert point["precipitation_window_hours"] == 6
    assert point["precipitation_rate_mm_h"] == 1.0
    assert point["fruiting_score"] > 0.7


def test_empty_met_payload_is_safe() -> None:
    result = build_temporal_forecast({"properties": {"timeseries": []}}, days=7)
    assert result["points"] == []
    assert result["days"] == []
    assert result["best_day"] is None
