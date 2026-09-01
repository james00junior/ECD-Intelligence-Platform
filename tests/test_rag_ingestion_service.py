from unittest.mock import MagicMock

from app.services.embedding_service import EmbeddingResult
from app.services.rag_ingestion_service import ingest_document


def _db_with_document(chunk_id=21):
    db = MagicMock()
    db.execute.return_value.first.return_value = (1,)
    db.execute.return_value.scalar_one.return_value = chunk_id
    return db


def test_ingest_document_stores_embedding_vectors_not_result_objects(monkeypatch):
    stored = []
    monkeypatch.setattr(
        "app.services.rag_ingestion_service.embed_documents_with_fallback",
        lambda texts, **kwargs: [
            EmbeddingResult(
                embedding=[0.1, 0.2, 0.3],
                provider="fixture",
                model="fixture-model",
                dimension=3,
            )
            for _ in texts
        ],
    )
    monkeypatch.setattr(
        "app.services.rag_ingestion_service.store_chunk_embedding",
        lambda db, chunk_id, embedding: stored.append(embedding),
    )
    monkeypatch.setattr(
        "app.services.rag_ingestion_service.chunk_document",
        lambda content: [MagicMock(chunk_index=0, content=content)],
    )

    result = ingest_document(
        db=_db_with_document(),
        organisation_id=1,
        document_id=9,
        content="SmartStart social franchise model.",
        embedding_provider="fixture",
    )

    assert result["chunks_created"] == 1
    assert stored == [[0.1, 0.2, 0.3]]
    assert isinstance(stored[0], list)


def test_ingest_document_rejects_missing_organisation_document():
    db = MagicMock()
    db.execute.return_value.first.return_value = None
    try:
        ingest_document(
            db=db,
            organisation_id=1,
            document_id=99,
            content="unused",
        )
    except ValueError as exc:
        assert "organisation" in str(exc).lower()
    else:
        raise AssertionError("Expected missing-document error")
