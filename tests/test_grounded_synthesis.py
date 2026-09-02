from unittest.mock import patch

from app.services.grounded_synthesis import (
    build_synthesis_prompt,
    synthesize_grounded_answer,
)


def _evidence(
    source_type="internal_document",
    organisation_id=1,
    content="Coaching supports programme quality.",
):
    return {
        "evidence_id": "evidence:1",
        "content": content,
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


def _sql_evidence():
    return {
        "evidence_id": "evidence:sql",
        "content": '[{"franchisee_count": 60}]',
        "provenance": {
            "source_type": "sql",
            "source_id": "sql:1",
            "title": "ECD operational database",
            "uri": None,
            "organisation_id": 1,
            "metadata": {
                "intent": "count_franchisees",
            },
        },
        "score": 1.0,
        "metadata": {},
    }


def test_prompt_contains_only_selected_evidence():
    prompt = build_synthesis_prompt(
        "What helps?",
        [_evidence()],
    )

    assert "Coaching supports programme quality." in prompt
    assert "unselected" not in prompt


def test_sql_evidence_is_rendered_as_natural_language():
    result = synthesize_grounded_answer(
        "How many franchisees?",
        [_sql_evidence()],
    )

    assert result["answer"] == (
        "There are currently 60 franchisees. [1]"
    )

    assert "[{\"franchisee_count\": 60}]" not in result["answer"]
    assert "{" not in result["answer"]
    assert "}" not in result["answer"]


def test_document_evidence_is_synthesized_not_dumped():
    llm_answer = (
        "The documentation indicates that coaching support "
        "is an important factor affecting programme quality. [1]"
    )

    with patch(
        "app.services.grounded_synthesis.complete_text"
    ) as complete_text:
        complete_text.return_value = type(
            "Result",
            (),
            {"text": llm_answer},
        )()

        result = synthesize_grounded_answer(
            "What affects programme quality?",
            [_evidence()],
        )

    assert result["answer"] == llm_answer
    assert result["answer"] != (
        "### Programme intelligence\n"
        "- Coaching supports programme quality. [1]"
    )

    complete_text.assert_called_once()


def test_mixed_sql_and_document_evidence_is_natural_language():
    llm_answer = (
        "The latest programme documentation indicates that "
        "coaching support is an important factor affecting "
        "programme quality. [2]"
    )

    with patch(
        "app.services.grounded_synthesis.complete_text"
    ) as complete_text:
        complete_text.return_value = type(
            "Result",
            (),
            {"text": llm_answer},
        )()

        result = synthesize_grounded_answer(
            (
                "How many franchisees are there, and "
                "what affects programme quality?"
            ),
            [
                _sql_evidence(),
                _evidence(),
            ],
        )

    assert (
        "There are currently 60 franchisees. [1]"
        in result["answer"]
    )

    assert llm_answer in result["answer"]

    assert "[{\"franchisee_count\": 60}]" not in result["answer"]
    assert "### Programme intelligence" not in result["answer"]


def test_llm_failure_does_not_dump_raw_document_chunks():
    with patch(
        "app.services.grounded_synthesis.complete_text",
        side_effect=RuntimeError("LLM unavailable"),
    ):
        result = synthesize_grounded_answer(
            "What affects programme quality?",
            [_evidence()],
        )

    assert result["answer"] is not None
    assert "Coaching supports programme quality." not in result["answer"]
    assert "### Programme intelligence" not in result["answer"]


def test_synthesis_distinguishes_external_evidence():
    external = synthesize_grounded_answer(
        "What helps?",
        [
            _evidence(
                source_type="external",
                organisation_id=None,
            )
        ],
    )

    assert (
        external["citations"][0]["source_kind"]
        == "external"
    )


def test_empty_evidence_returns_error():
    result = synthesize_grounded_answer(
        "What helps?",
        [],
    )

    assert result["answer"] is None
    assert result["error"] == (
        "Insufficient evidence to answer the question."
    )