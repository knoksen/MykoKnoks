from app.services.model_registry import get_model, list_models


def test_registry_exposes_spatial_and_temporal_models() -> None:
    models = list_models()
    ids = {model["id"] for model in models}
    assert "semilanceata-gis-heuristic-v1" in ids
    assert "weather-memory-fruiting-heuristic-v1" in ids
    assert "fungal-sdm-spatial-cv-v1-candidate" in ids


def test_heuristic_is_not_claimed_calibrated() -> None:
    model = get_model("semilanceata-gis-heuristic-v1")
    assert model is not None
    assert model["trained"] is False
    assert model["calibrated"] is False
    assert "Not occurrence probability" in model["semantics"]


def test_spatial_candidate_does_not_use_forecast_weather_features() -> None:
    model = get_model("fungal-sdm-spatial-cv-v1-candidate")
    assert model is not None
    assert "antecedent_precip_72h_mm" not in model["feature_contract"]
    assert "slope_deg" in model["feature_contract"]

    temporal = get_model("weather-memory-fruiting-heuristic-v1")
    assert temporal is not None
    assert "antecedent_precip_72h_mm" in temporal["feature_contract"]
