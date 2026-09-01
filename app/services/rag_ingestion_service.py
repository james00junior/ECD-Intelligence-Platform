from __future__ import annotations

import hashlib
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.chunking_service import chunk_document
from app.services.embedding_service import embed_documents
from app.services.vector_service import store_chunk_embedding


def _content_hash(content: str) -> str:
    """
    Create a deterministic SHA-256 hash for content.
    """

    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


def ingest_document(
    db: Session,
    organisation_id: int,
    document_id: int,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> dict:
    """
    Chunk a document, generate embeddings, and store the
    chunks in PostgreSQL/pgvector.

    The document must belong to the supplied organisation.
    """

    metadata = metadata or {}

    document_query = text(
        """
        SELECT id
        FROM documents
        WHERE id = :document_id
          AND organisation_id = :organisation_id
        """
    )

    document = db.execute(
        document_query,
        {
            "document_id": document_id,
            "organisation_id": organisation_id,
        },
    ).first()

    if document is None:
        raise ValueError(
            "Document does not exist for this organisation."
        )

    chunks = chunk_document(content)

    if not chunks:
        return {
            "document_id": document_id,
            "chunks_created": 0,
            "embeddings_created": 0,
        }

    insert_chunk_query = text(
        """
        INSERT INTO document_chunks (
            organisation_id,
            document_id,
            chunk_index,
            content,
            content_hash,
            metadata
        )
        VALUES (
            :organisation_id,
            :document_id,
            :chunk_index,
            :content,
            :content_hash,
            CAST(:metadata AS json)
        )
        RETURNING id
        """
    )

    chunk_records: list[dict] = []

    try:
        for chunk in chunks:
            chunk_metadata = {
                **metadata,
                "chunk_index": chunk.chunk_index,
            }

            result = db.execute(
                insert_chunk_query,
                {
                    "organisation_id": organisation_id,
                    "document_id": document_id,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "content_hash": _content_hash(
                        chunk.content
                    ),
                    "metadata": __import__(
                        "json"
                    ).dumps(chunk_metadata),
                },
            )

            chunk_id = result.scalar_one()

            chunk_records.append(
                {
                    "chunk_id": chunk_id,
                    "content": chunk.content,
                }
            )

        db.flush()

        embeddings = embed_documents(
            [
                chunk["content"]
                for chunk in chunk_records
            ]
        )

        for chunk, embedding in zip(
            chunk_records,
            embeddings,
        ):
            store_chunk_embedding(
                db=db,
                chunk_id=chunk["chunk_id"],
                embedding=embedding,
            )

    except Exception:
        db.rollback()
        raise

    return {
        "document_id": document_id,
        "chunks_created": len(chunk_records),
        "embeddings_created": len(chunk_records),
    }