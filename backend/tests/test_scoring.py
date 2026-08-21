from app.scoring import (
    HabitatFeatures,
    WeatherFeatures,
    combine_scores,
    fruiting_score,
    habitat_score,
)


def test_scores_are_bounded():
    h, _ = habitat_score(HabitatFeatures(1.0, 1.0, 1.0, 10.0))
    f, _ = fruiting_score(WeatherFeatures(11.0, 95.0, 4.0))
    assert 0 <= h <= 1
    assert 0 <= f <= 1
    assert 0 <= combine_scores(h, f) <= 1


def test_combination_is_multiplicative():
    assert combine_scores(0.8, 0.5) == 0.4
