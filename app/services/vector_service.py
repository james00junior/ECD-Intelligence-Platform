from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


def _validate_embedding(
    embedding: list[float],
    name: str = "Embedding",
) -> None:
    """
    Validate an embedding without imposing a fixed dimension.

    Dimension is intentionally discovered from the actual vector.
    pgvector remains responsible for vector compatibility.
    """

    if not embedding:
        raise ValueError(
            f"{name} cannot be empty."
        )

    if not all(
        isinstance(value, (int, float))
        for value in embedding
    ):
        raise ValueError(
            f"{name} must contain only numeric values."
        )


def embedding_dimension(
    embedding: list[float],
) -> int:
    """
    Discover the dimension of an embedding dynamically.
    """

    _validate_embedding(embedding)

    return len(embedding)


def store_chunk_embedding(
    db: Session,
    chunk_id: int,
    embedding: list[float],
) -> None:
    """
    Store an embedding for an existing document chunk.

    No embedding dimension is hard-coded.

    The dimension is discovered from the supplied embedding and
    PostgreSQL/pgvector stores the vector without imposing a
    fixed application-level dimension.
    """

    _validate_embedding(embedding)

    query = text(
        """
        UPDATE document_chunks
        SET embedding = CAST(:embedding AS vector)
        WHERE id = :chunk_id
        """
    )

    result = db.execute(
        query,
        {
            "chunk_id": chunk_id,
            "embedding": embedding,
        },
    )

    if result.rowcount == 0:
        raise ValueError(
            f"Document chunk {chunk_id} does not exist."
        )

    db.commit()


def search_similar_chunks(
    db: Session,
    organisation_id: int,
    query_embedding: list[float],
    limit: int = 5,
) -> list[dict]:
    """
    Retrieve semantically similar document chunks.

    The query embedding dimension is discovered dynamically.

    Only stored vectors with the same dimension as the query
    vector are considered. This prevents pgvector dimension
    mismatch errors while allowing different embedding models
    and dimensions to coexist in the database.
    """

    _validate_embedding(
        query_embedding,
        name="Query embedding",
    )

    if limit <= 0:
        raise ValueError(
            "limit must be greater than zero."
        )

    query = text(
        """
        SELECT
            dc.id AS chunk_id,
            dc.document_id,
            dc.organisation_id,
            dc.chunk_index,
            dc.content,
            dc.content_hash,
            dc.metadata,
            vector_dims(dc.embedding)
                AS embedding_dimension,
            d.title,
            d.source_uri,
            1 - (
                dc.embedding
                <=> CAST(:embedding AS vector)
            ) AS similarity
        FROM document_chunks dc
        JOIN documents d
            ON d.id = dc.document_id
        WHERE dc.organisation_id = :organisation_id
          AND d.organisation_id = :organisation_id
          AND dc.embedding IS NOT NULL
          AND vector_dims(dc.embedding)
              = vector_dims(CAST(:embedding AS vector))
        ORDER BY
            dc.embedding
            <=> CAST(:embedding AS vector)
        LIMIT :limit
        """
    )

    rows = (
        db.execute(
            query,
            {
                "organisation_id": organisation_id,
                "embedding": query_embedding,
                "limit": limit,
            },
        )
        .mappings()
        .all()
    )

    return [dict(row) for row in rows]


def delete_chunk_embedding(
    db: Session,
    chunk_id: int,
) -> None:
    """
    Remove the embedding from a document chunk.
    """

    query = text(
        """
        UPDATE document_chunks
        SET embedding = NULL
        WHERE id = :chunk_id
        """
    )

    db.execute(
        query,
        {
            "chunk_id": chunk_id,
        },
    )

    db.commit()