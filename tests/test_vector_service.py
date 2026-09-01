from unittest.mock import MagicMock

import pytest

from app.services.vector_service import (
    delete_chunk_embedding,
    embedding_dimension,
    search_similar_chunks,
    store_chunk_embedding,
)


def test_embedding_dimension_is_discovered_dynamically():
    embedding = [0.1, 0.2, 0.3, 0.4, 0.5]

    assert embedding_dimension(embedding) == 5


def test_embedding_dimension_rejects_empty_embedding():
    with pytest.raises(
        ValueError,
        match="(?i)embedding",
    ):
        embedding_dimension([])


def test_store_chunk_embedding_accepts_dynamic_dimension():
    db = MagicMock()

    result = MagicMock()
    result.rowcount = 1

    db.execute.return_value = result

    embedding = [0.1, 0.2, 0.3]

    store_chunk_embedding(
        db=db,
        chunk_id=1,
        embedding=embedding,
    )

    db.execute.assert_called_once()
    db.commit.assert_called_once()


def test_store_chunk_embedding_rejects_empty_embedding():
    db = MagicMock()

    with pytest.raises(
        ValueError,
        match="(?i)embedding",
    ):
        store_chunk_embedding(
            db=db,
            chunk_id=1,
            embedding=[],
        )

    db.execute.assert_not_called()
    db.commit.assert_not_called()


def test_store_chunk_embedding_rejects_non_numeric_embedding():
    db = MagicMock()

    with pytest.raises(
        ValueError,
        match="numeric",
    ):
        store_chunk_embedding(
            db=db,
            chunk_id=1,
            embedding=[
                0.1,
                "invalid",
                0.3,
            ],
        )

    db.execute.assert_not_called()
    db.commit.assert_not_called()


def test_store_chunk_embedding_rejects_missing_chunk():
    db = MagicMock()

    result = MagicMock()
    result.rowcount = 0

    db.execute.return_value = result

    with pytest.raises(
        ValueError,
        match="Document chunk 999 does not exist",
    ):
        store_chunk_embedding(
            db=db,
            chunk_id=999,
            embedding=[0.1, 0.2, 0.3],
        )

    db.commit.assert_not_called()


def test_search_similar_chunks_returns_results():
    db = MagicMock()

    rows = [
        {
            "chunk_id": 1,
            "document_id": 10,
            "organisation_id": 1,
            "chunk_index": 0,
            "content": "ECD programmes support children.",
            "content_hash": "abc123",
            "metadata": {},
            "embedding_dimension": 3,
            "title": "ECD Programme",
            "source_uri": "test://document",
            "similarity": 0.95,
        }
    ]

    (
        db.execute
        .return_value
        .mappings
        .return_value
        .all
        .return_value
    ) = rows

    results = search_similar_chunks(
        db=db,
        organisation_id=1,
        query_embedding=[0.1, 0.2, 0.3],
        limit=5,
    )

    assert len(results) == 1
    assert results[0]["chunk_id"] == 1
    assert results[0]["embedding_dimension"] == 3
    assert results[0]["similarity"] == 0.95


def test_search_similar_chunks_returns_empty_results():
    db = MagicMock()

    (
        db.execute
        .return_value
        .mappings
        .return_value
        .all
        .return_value
    ) = []

    results = search_similar_chunks(
        db=db,
        organisation_id=1,
        query_embedding=[0.1, 0.2, 0.3],
        limit=5,
    )

    assert results == []


def test_search_rejects_empty_embedding():
    db = MagicMock()

    with pytest.raises(
        ValueError,
        match="(?i)query embedding",
    ):
        search_similar_chunks(
            db=db,
            organisation_id=1,
            query_embedding=[],
            limit=5,
        )

    db.execute.assert_not_called()


def test_search_rejects_non_numeric_embedding():
    db = MagicMock()

    with pytest.raises(
        ValueError,
        match="numeric",
    ):
        search_similar_chunks(
            db=db,
            organisation_id=1,
            query_embedding=[
                0.1,
                "invalid",
                0.3,
            ],
            limit=5,
        )

    db.execute.assert_not_called()


def test_search_rejects_invalid_limit():
    db = MagicMock()

    with pytest.raises(
        ValueError,
        match="limit",
    ):
        search_similar_chunks(
            db=db,
            organisation_id=1,
            query_embedding=[0.1, 0.2, 0.3],
            limit=0,
        )

    db.execute.assert_not_called()


def test_delete_chunk_embedding():
    db = MagicMock()

    delete_chunk_embedding(
        db=db,
        chunk_id=1,
    )

    db.execute.assert_called_once()
    db.commit.assert_called_once()