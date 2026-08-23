from app.scoring import HabitatFeatures
from app.services.gis_features import normalize_gis_evidence, prediction_habitat_score


def test_normalizes_structured_ar5_sr16_ngu_evidence():
    vector = normalize_gis_evidence(
        {"features": [{"properties": {"arealtype": 23, "beskrivelse": "Innmarksbeite"}}]},
        {"features": [{"properties": {"treslag": "Gran", "hoyde": 14.2}}]},
        {"features": [{"properties": {"losmassetype": "Torv og myr"}}]},
    )
    data = vector.as_dict()
    assert data["ar5_code"] == 23
    assert data["open_land_score"] > 0.9
    assert data["dominant_tree"] == "Gran"
    assert data["forest_height_m"] == 14.2
    assert data["substrate_moisture_score"] > 0.8
    assert data["coverage"] == 0.75


def test_semilanceata_profile_is_explicit_and_explainable():
    habitat = HabitatFeatures(grassland=0.8, forest_edge=0.3, soil_moisture_proxy=0.7, elevation_m=80)
    gis = {
        "coverage": 0.75,
        "open_land_score": 0.95,
        "substrate_moisture_score": 0.82,
        "forest_score": 0.05,
    }
    score, components, drivers = prediction_habitat_score("Psilocybe semilanceata", habitat, gis)
    assert 0 <= score <= 1
    assert components["profile"] == "semilanceata-gis-heuristic-v0.9"
    assert components["open_land"] == 0.95
    assert any("v0.9" in driver for driver in drivers)


def test_unknown_taxon_keeps_generic_legacy_score():
    habitat = HabitatFeatures(grassland=0.7, forest_edge=0.5, soil_moisture_proxy=0.6, elevation_m=120)
    score, components, drivers = prediction_habitat_score(
        "Unmodelled species",
        habitat,
        {"coverage": 0.75, "open_land_score": 0.1, "forest_score": 0.9},
    )
    assert 0 <= score <= 1
    assert components["profile"] == "generic-legacy-v0.9"
    assert any("no taxon-specific" in driver for driver in drivers)
