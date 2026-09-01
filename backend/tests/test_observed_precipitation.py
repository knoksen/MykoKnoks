from datetime import UTC, datetime

import pytest

from app.clients.frost import FrostClient
from app.services.observed_precipitation import ObservedPrecipitationService


class FakeFrostClient:
    DAILY_PRECIPITATION_ELEMENT = FrostClient.DAILY_PRECIPITATION_ELEMENT

    async def nearest_precipitation_sources(
        self,
        lat: float,
        lon: float,
        *,
        max_count: int = 3,
    ) -> list[dict]:
        assert lat == 58.735
        assert lon == 5.647
        assert max_count == 2
        return [
            {"id": "SN11111", "name": "Near dry station", "distance": 1.2},
            {"id": "SN22222", "name": "Near wet station", "distance": 3.4},
        ]

    async def daily_precipitation(self, sources, *, start, end, qualities="0,1,2,3,4"):
        assert qualities == "0,1,2,3,4"
        if sources == ["SN11111"]:
            return []
        assert sources == ["SN22222"]
        rows = []
        for day, amount in enumerate((0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0), start=1):
            rows.append(
                {
                    "sourceId": "SN22222:0",
                    "referenceTime": f"2026-08-{day + 24:02d}T06:00:00.000Z",
                    "observations": [
                        {
                            "elementId": FrostClient.DAILY_PRECIPITATION_ELEMENT,
                            "value": amount,
                            "qualityCode": 0,
                            "timeOffset": "PT6H",
                            "timeResolution": "P1D",
                        }
                    ],
                }
            )
        return rows


@pytest.mark.asyncio
async def test_observed_precipitation_uses_first_nearest_station_with_data() -> None:
    service = ObservedPrecipitationService(FakeFrostClient(), nearest_station_count=2)
    result = await service.history(
        58.735,
        5.647,
        days=7,
        now=datetime(2026, 9, 1, 10, 0, tzinfo=UTC),
    )

    assert result["available"] is True
    assert result["observed"] is True
    assert result["source"]["id"] == "SN22222"
    assert result["source"]["distance_km"] == 3.4
    assert result["antecedent_precip_24h_standard_mm"] == 6.0
    assert result["antecedent_precip_72h_standard_mm"] == 15.0
    assert result["antecedent_precip_168h_standard_mm"] == 21.0
    assert result["data_quality"]["daily_periods_available"] == 7
    assert "not rolling" in result["aggregation_semantics"]
    assert result["probability_claim_allowed"] is False


@pytest.mark.asyncio
async def test_missing_frost_client_id_is_explicitly_unavailable() -> None:
    service = ObservedPrecipitationService(FrostClient(None), nearest_station_count=3)
    result = await service.history(
        58.735,
        5.647,
        now=datetime(2026, 9, 1, 10, 0, tzinfo=UTC),
    )

    assert result == {
        "available": False,
        "provider": "MET Norway Frost",
        "reason": "FROST_CLIENT_ID not configured",
        "observed": False,
        "probability_claim_allowed": False,
    }
