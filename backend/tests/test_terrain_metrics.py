from app.services.terrain_metrics import derive_terrain_metrics


def test_flat_stencil_has_zero_slope_and_roughness() -> None:
    metrics = derive_terrain_metrics(100, 100, 100, 100, 100, spacing_m=50)
    assert metrics.slope_deg == 0
    assert metrics.roughness_m == 0
    assert metrics.sample_count == 5


def test_east_west_gradient_produces_slope() -> None:
    metrics = derive_terrain_metrics(100, 100, 100, 110, 90, spacing_m=50)
    assert 10 < metrics.slope_deg < 12
    assert metrics.roughness_m > 0
