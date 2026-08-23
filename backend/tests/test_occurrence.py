from app.services.occurrence import occurrence_context


def test_occurrence_context_counts_matching_presence_records():
    payload = {
        "items": [
            {"scientificName": "Psilocybe semilanceata", "id": 1},
            {"scientificName": "Cantharellus cibarius", "id": 2},
            {"taxon": {"scientificName": "Psilocybe semilanceata"}, "id": 3},
        ]
    }
    context = occurrence_context(payload, "Psilocybe semilanceata")
    assert context.records_examined == 3
    assert context.matching_records == 2
    assert context.support_index > 0
    assert "presence-only" in context.interpretation


def test_zero_occurrence_match_is_not_absence_evidence():
    context = occurrence_context([{"scientificName": "Other species"}], "Psilocybe semilanceata")
    assert context.matching_records == 0
    assert context.support_index == 0
    assert "not absence evidence" in context.interpretation
