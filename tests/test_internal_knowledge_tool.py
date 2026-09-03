from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.tools.internal_knowledge_tool import (
    canonicalize_source_uri,
    search_internal_knowledge,
    select_diverse_chunks,
)


def _chunk(organisation_id=1):
    return {
        "chunk_id": 7,
        "document_id": 3,
        "organisation_id": organisation_id,
        "chunk_index": 2,
        "content": "Coaching improves programme quality.",
        "content_hash": "hash",
        "metadata": {"page": 4},
        "embedding_dimension": 3,
        "title": "Programme Quality Report",
        "source_uri": "document://quality-report",
        "similarity": 0.93,
    }


# ---------------------------------------------------------------------------
# URL canonicalisation
# ---------------------------------------------------------------------------


def test_canonicalize_source_uri():
    assert (
        canonicalize_source_uri(
            "https://SmartStart.org.za/about-us/"
        )
        == "https://smartstart.org.za/about-us"
    )

    assert (
        canonicalize_source_uri(
            "https://smartstart.org.za/about-us/#programme"
        )
        == "https://smartstart.org.za/about-us"
    )

    assert (
        canonicalize_source_uri(
            "https://smartstart.org.za/about-us/?utm_source=test"
        )
        == "https://smartstart.org.za/about-us"
    )


def test_canonicalize_source_uri_preserves_meaningful_query():
    assert (
        canonicalize_source_uri(
            "https://example.org/search?q=ecd&utm_source=test"
        )
        == "https://example.org/search?q=ecd"
    )


def test_canonicalize_source_uri_root():
    assert (
        canonicalize_source_uri("https://smartstart.org.za/")
        == "https://smartstart.org.za/"
    )


def test_canonicalize_source_uri_empty():
    assert canonicalize_source_uri(None) is None
    assert canonicalize_source_uri("") is None


# ---------------------------------------------------------------------------
# Internal knowledge retrieval
# ---------------------------------------------------------------------------


def test_returns_evidence_with_provenance(monkeypatch):
    monkeypatch.setattr(
        "app.tools.internal_knowledge_tool.embed_text",
        lambda question: SimpleNamespace(
            embedding=[0.1, 0.2, 0.3]
        ),
    )

    search = MagicMock(return_value=[_chunk()])

    monkeypatch.setattr(
        "app.tools.internal_knowledge_tool.search_similar_chunks",
        search,
    )

    evidence = search_internal_knowledge(
        "What improves quality?",
        1,
        MagicMock(),
    )

    assert evidence[0]["evidence_id"] == "document-chunk:7"
    assert evidence[0]["score"] == 0.93
    assert evidence[0]["provenance"]["organisation_id"] == 1
    assert evidence[0]["provenance"]["metadata"]["chunk_index"] == 2
    assert search.call_args.kwargs["organisation_id"] == 1


def test_does_not_return_cross_organisation_rows(monkeypatch):
    monkeypatch.setattr(
        "app.tools.internal_knowledge_tool.embed_text",
        lambda question: SimpleNamespace(
            embedding=[0.1]
        ),
    )

    monkeypatch.setattr(
        "app.tools.internal_knowledge_tool.search_similar_chunks",
        lambda **kwargs: [_chunk(organisation_id=2)],
    )

    assert search_internal_knowledge(
        "Question",
        1,
        MagicMock(),
    ) == []


@pytest.mark.parametrize(
    "question, organisation_id",
    [
        ("", 1),
        ("Question", 0),
    ],
)
def test_rejects_missing_question_or_organisation(
    question,
    organisation_id,
):
    with pytest.raises(ValueError):
        search_internal_knowledge(
            question,
            organisation_id,
            MagicMock(),
        )


def test_search_deduplicates_exact_duplicate_chunks(monkeypatch):
    monkeypatch.setattr(
        "app.tools.internal_knowledge_tool.embed_text",
        lambda question: SimpleNamespace(
            embedding=[0.1, 0.2, 0.3]
        ),
    )

    first = _chunk()

    duplicate = _chunk()
    duplicate["chunk_id"] = 99
    duplicate["source_uri"] = "document://quality-report/"

    monkeypatch.setattr(
        "app.tools.internal_knowledge_tool.search_similar_chunks",
        lambda **kwargs: [first, duplicate],
    )

    evidence = search_internal_knowledge(
        "What improves quality?",
        1,
        MagicMock(),
    )

    assert len(evidence) == 1


def test_search_retains_different_chunks_from_same_document(monkeypatch):
    monkeypatch.setattr(
        "app.tools.internal_knowledge_tool.embed_text",
        lambda question: SimpleNamespace(
            embedding=[0.1, 0.2, 0.3]
        ),
    )

    first = _chunk()

    second = _chunk()
    second["chunk_id"] = 8
    second["chunk_index"] = 3
    second["content"] = "Different evidence."
    second["content_hash"] = "different-hash"
    second["similarity"] = 0.90

    monkeypatch.setattr(
        "app.tools.internal_knowledge_tool.search_similar_chunks",
        lambda **kwargs: [first, second],
    )

    evidence = search_internal_knowledge(
        "What improves quality?",
        1,
        MagicMock(),
    )

    assert len(evidence) == 2
    assert evidence[0]["provenance"]["metadata"]["chunk_id"] == 7
    assert evidence[1]["provenance"]["metadata"]["chunk_id"] == 8


# ---------------------------------------------------------------------------
# Document-level diversity
# ---------------------------------------------------------------------------


def test_select_diverse_chunks_prefers_new_document_when_scores_are_close():
    chunks = [
        {
            "chunk_id": 1,
            "document_id": 10,
            "similarity": 0.91,
        },
        {
            "chunk_id": 2,
            "document_id": 10,
            "similarity": 0.90,
        },
        {
            "chunk_id": 3,
            "document_id": 20,
            "similarity": 0.89,
        },
        {
            "chunk_id": 4,
            "document_id": 30,
            "similarity": 0.88,
        },
    ]

    selected = select_diverse_chunks(
        chunks,
        limit=3,
    )

    assert [chunk["document_id"] for chunk in selected] == [
        10,
        20,
        30,
    ]


def test_select_diverse_chunks_allows_multiple_chunks_when_score_is_better():
    chunks = [
        {
            "chunk_id": 1,
            "document_id": 10,
            "similarity": 0.95,
        },
        {
            "chunk_id": 2,
            "document_id": 10,
            "similarity": 0.94,
        },
        {
            "chunk_id": 3,
            "document_id": 20,
            "similarity": 0.80,
        },
    ]

    selected = select_diverse_chunks(
        chunks,
        limit=2,
    )

    assert [chunk["document_id"] for chunk in selected] == [
        10,
        10,
    ]


def test_select_diverse_chunks_respects_limit():
    chunks = [
        {
            "chunk_id": 1,
            "document_id": 10,
            "similarity": 0.95,
        },
        {
            "chunk_id": 2,
            "document_id": 20,
            "similarity": 0.94,
        },
        {
            "chunk_id": 3,
            "document_id": 30,
            "similarity": 0.93,
        },
    ]

    selected = select_diverse_chunks(
        chunks,
        limit=2,
    )

    assert len(selected) == 2
