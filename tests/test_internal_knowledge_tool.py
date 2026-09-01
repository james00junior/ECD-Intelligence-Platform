from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.tools.internal_knowledge_tool import search_internal_knowledge


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


def test_returns_evidence_with_provenance(monkeypatch):
    monkeypatch.setattr(
        "app.tools.internal_knowledge_tool.embed_text",
        lambda question: SimpleNamespace(embedding=[0.1, 0.2, 0.3]),
    )
    search = MagicMock(return_value=[_chunk()])
    monkeypatch.setattr("app.tools.internal_knowledge_tool.search_similar_chunks", search)

    evidence = search_internal_knowledge(
        "What improves quality?", 1, MagicMock()
    )

    assert evidence[0]["evidence_id"] == "document-chunk:7"
    assert evidence[0]["score"] == 0.93
    assert evidence[0]["provenance"]["organisation_id"] == 1
    assert evidence[0]["provenance"]["metadata"]["chunk_index"] == 2
    assert search.call_args.kwargs["organisation_id"] == 1


def test_does_not_return_cross_organisation_rows(monkeypatch):
    monkeypatch.setattr(
        "app.tools.internal_knowledge_tool.embed_text",
        lambda question: SimpleNamespace(embedding=[0.1]),
    )
    monkeypatch.setattr(
        "app.tools.internal_knowledge_tool.search_similar_chunks",
        lambda **kwargs: [_chunk(organisation_id=2)],
    )

    assert search_internal_knowledge("Question", 1, MagicMock()) == []


@pytest.mark.parametrize("question, organisation_id", [("", 1), ("Question", 0)])
def test_rejects_missing_question_or_organisation(question, organisation_id):
    with pytest.raises(ValueError):
        search_internal_knowledge(question, organisation_id, MagicMock())
