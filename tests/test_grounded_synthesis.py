from app.services.grounded_synthesis import (
    build_synthesis_prompt,
    synthesize_grounded_answer,
)


def _evidence(source_type="internal_document", organisation_id=1):
    return {
        "evidence_id": "evidence:1",
        "content": "Coaching supports programme quality.",
        "provenance": {
            "source_type": source_type,
            "source_id": "source:1",
            "title": "Programme report",
            "uri": "https://example.com/report",
            "organisation_id": organisation_id,
            "metadata": {},
        },
        "score": 0.9,
        "metadata": {},
    }


def test_prompt_contains_only_selected_evidence():
    prompt = build_synthesis_prompt("What helps?", [_evidence()])
    assert "Coaching supports programme quality." in prompt
    assert "unselected" not in prompt


def test_synthesis_returns_grounded_answer_and_citation():
    result = synthesize_grounded_answer("What helps?", [_evidence()])

    assert "Coaching supports programme quality." in result["answer"]
    assert "[1]" in result["answer"]
    assert result["citations"][0]["source_kind"] == "organisational"
    assert result["error"] is None


def test_synthesis_distinguishes_external_evidence_and_handles_empty_evidence():
    external = synthesize_grounded_answer("What helps?", [_evidence("external", None)])
    empty = synthesize_grounded_answer("What helps?", [])

    assert external["citations"][0]["source_kind"] == "external"
    assert empty["answer"] is None
    assert empty["error"] == "Insufficient evidence to answer the question."
