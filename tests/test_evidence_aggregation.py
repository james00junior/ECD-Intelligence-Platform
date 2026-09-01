from app.services.evidence_aggregation import aggregate_evidence


def _evidence(identifier, source_type, organisation_id, content, score=None, **metadata):
    return {
        "evidence_id": identifier,
        "content": content,
        "provenance": {
            "source_type": source_type,
            "source_id": identifier,
            "title": identifier,
            "uri": None,
            "organisation_id": organisation_id,
            "metadata": {},
        },
        "score": score,
        "metadata": metadata,
    }


def test_combines_and_ranks_tenant_safe_evidence():
    internal = _evidence("document:1", "internal_document", 1, "Internal", 0.9)
    sql = _evidence("sql:1", "sql", 1, "SQL")
    external = _evidence("external:1", "external", None, "External")

    result = aggregate_evidence([external, internal, sql], organisation_id=1)

    assert [item["evidence_id"] for item in result["selected_evidence"]] == [
        "sql:1", "document:1", "external:1"
    ]
    assert result["rejected_evidence"] == []


def test_rejects_cross_organisation_and_duplicate_evidence():
    safe = _evidence("document:1", "internal_document", 1, "Internal")
    duplicate = _evidence("document:1", "internal_document", 1, "Internal")
    foreign = _evidence("document:2", "internal_document", 2, "Foreign")

    result = aggregate_evidence([safe, duplicate, foreign], organisation_id=1)

    assert result["selected_evidence"] == [safe]
    assert result["rejected_evidence"] == [duplicate, foreign]


def test_reports_conflicting_claims():
    first = _evidence("sql:1", "sql", 1, "Count is 4", claim_key="franchisee_count")
    second = _evidence("document:1", "internal_document", 1, "Count is 5", claim_key="franchisee_count")

    result = aggregate_evidence([first, second], organisation_id=1)

    assert result["conflicts"] == [{
        "claim_key": "franchisee_count",
        "evidence_ids": ["sql:1", "document:1"],
    }]
