from app.workflows.research_workflow import (
    PENDING_ROUTE,
    initial_routing_node,
    research_workflow,
)


def test_initial_routing_node_preserves_existing_evidence():
    evidence = [
        {
            "evidence_id": "document-chunk-1",
            "content": "Programme quality improves with support.",
            "provenance": {
                "source_type": "internal_document",
                "source_id": "chunk-1",
                "title": "Programme guide",
                "uri": "document://programme-guide",
                "organisation_id": 1,
                "metadata": {},
            },
            "score": 0.91,
            "metadata": {},
        }
    ]

    result = initial_routing_node(
        {
            "question": "What improves programme quality?",
            "organisation_id": 1,
            "evidence": evidence,
            "research_steps": 1,
        }
    )

    assert result["route"] == PENDING_ROUTE
    assert result["evidence"] == evidence
    assert result["research_steps"] == 1
    assert result["error"] is None


def test_research_workflow_terminates_with_empty_evidence():
    result = research_workflow.invoke(
        {
            "question": "What improves programme quality?",
            "organisation_id": 1,
        }
    )

    assert result["route"] == PENDING_ROUTE
    assert result["evidence"] == []
    assert result["research_steps"] == 0
    assert result["answer"] is None
    assert result["error"] is None


def test_research_workflow_preserves_organisation_scope():
    result = research_workflow.invoke(
        {
            "question": "Summarise the organisation's programme guide.",
            "organisation_id": 42,
        }
    )

    assert result["organisation_id"] == 42
    assert result["route"] == PENDING_ROUTE
