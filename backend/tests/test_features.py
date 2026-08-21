from app.services.features import proxies_from_evidence


def test_real_evidence_proxies():
    grass, edge, moisture, drivers = proxies_from_evidence(
        "Dyrka mark",
        {"arealtype": "Fulldyrka jord"},
        {"treslag": "Gran"},
        {"losmassetype": "Torv og myr"},
    )
    assert grass > 0.8
    assert edge > 0.6
    assert moisture > 0.7
    assert len(drivers) >= 3
