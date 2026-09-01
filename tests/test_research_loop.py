from app.services.research_loop import (
    evaluate_evidence_sufficiency,
    refine_research_query,
)


def test_evidence_is_sufficient_when_selected_evidence_exists():
    decision = evaluate_evidence_sufficiency([{"evidence_id": "1"}], [], None, 1, 6, True)
    assert decision["sufficient"] is True
    assert decision["should_retry"] is False


def test_empty_evidence_retries_before_step_limit():
    decision = evaluate_evidence_sufficiency([], [], None, 1, 2, True)
    assert decision["should_retry"] is True
    assert "refined" in decision["reason"]


def test_loop_stops_for_conflicts_errors_and_step_limit():
    conflict = evaluate_evidence_sufficiency([], [{"claim_key": "count"}], None, 1, 6, True)
    failure = evaluate_evidence_sufficiency([], [], "provider failed", 1, 6, True)
    limit = evaluate_evidence_sufficiency([], [], None, 2, 2, True)

    assert conflict["should_retry"] is False
    assert failure["reason"] == "provider failed"
    assert "limit" in limit["reason"]


def test_refines_query_deterministically():
    assert refine_research_query("What helps?", 0) == "What helps?"
    assert refine_research_query("What helps?", 1).endswith("supporting evidence.")
