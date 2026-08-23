from app.services.model_registry import get_model, list_models


def test_registry_exposes_heuristic_and_candidate() -> None:
    models = list_models()
    ids = {model["id"] for model in models}
    assert "semilanceata-gis-heuristic-v1" in ids
    assert "fungal-sdm-spatial-cv-v1-candidate" in ids


def test_heuristic_is_not_claimed_calibrated() -> None:
    model = get_model("semilanceata-gis-heuristic-v1")
    assert model is not None
    assert model["trained"] is False
    assert model["calibrated"] is False
    assert "Not occurrence probability" in model["semantics"]
