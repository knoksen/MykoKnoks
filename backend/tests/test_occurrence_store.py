from sqlalchemy import create_engine

from app.repositories.occurrence_store import OccurrenceStoreRepository, normalize_occurrence


def test_occurrence_normalization_and_upsert() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    repository = OccurrenceStoreRepository("sqlite+pysqlite:///:memory:", engine=engine)
    record = normalize_occurrence(
        {
            "id": "abc-123",
            "scientificName": "Psilocybe semilanceata",
            "decimalLatitude": 58.735,
            "decimalLongitude": 5.647,
            "coordinateUncertaintyInMeters": 12,
            "eventDate": "2026-08-20",
        }
    )

    assert record.h3 is not None
    assert record.source_record_id == "artskart:abc-123"
    assert repository.upsert_many([record]) == 1
    assert repository.count() == 1
    assert repository.count("Psilocybe semilanceata") == 1

    assert repository.upsert_many([record]) == 1
    assert repository.count() == 1
