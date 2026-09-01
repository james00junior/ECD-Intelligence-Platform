from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


def create_knowledge_source(
    db: Session,
    organisation_id: int,
    name: str,
    source_type: str,
    base_url: str | None = None,
) -> dict:
    query = text(
        """
        INSERT INTO knowledge_sources (
            organisation_id,
            name,
            source_type,
            base_url
        )
        VALUES (
            :organisation_id,
            :name,
            :source_type,
            :base_url
        )
        RETURNING
            id,
            organisation_id,
            name,
            source_type,
            base_url
        """
    )

    row = db.execute(
        query,
        {
            "organisation_id": organisation_id,
            "name": name,
            "source_type": source_type,
            "base_url": base_url,
        },
    ).mappings().first()

    db.commit()

    if row is None:
        raise RuntimeError(
            "Knowledge source could not be created."
        )

    return dict(row)


def create_document(
    db: Session,
    organisation_id: int,
    knowledge_source_id: int,
    title: str,
    document_type: str,
    source_uri: str,
    content_hash: str | None = None,
    status: str = "active",
) -> dict:
    query = text(
        """
        INSERT INTO documents (
            organisation_id,
            knowledge_source_id,
            title,
            document_type,
            source_uri,
            content_hash,
            status
        )
        VALUES (
            :organisation_id,
            :knowledge_source_id,
            :title,
            :document_type,
            :source_uri,
            :content_hash,
            :status
        )
        RETURNING
            id,
            organisation_id,
            knowledge_source_id,
            title,
            document_type,
            source_uri,
            content_hash,
            status
        """
    )

    row = db.execute(
        query,
        {
            "organisation_id": organisation_id,
            "knowledge_source_id": knowledge_source_id,
            "title": title,
            "document_type": document_type,
            "source_uri": source_uri,
            "content_hash": content_hash,
            "status": status,
        },
    ).mappings().first()

    db.commit()

    if row is None:
        raise RuntimeError(
            "Document could not be created."
        )

    return dict(row)


def list_documents(
    db: Session,
    organisation_id: int,
) -> list[dict]:
    query = text(
        """
        SELECT
            id,
            organisation_id,
            knowledge_source_id,
            title,
            document_type,
            source_uri,
            content_hash,
            status
        FROM documents
        WHERE organisation_id = :organisation_id
        ORDER BY id
        """
    )

    rows = db.execute(
        query,
        {
            "organisation_id": organisation_id,
        },
    ).mappings().all()

    return [dict(row) for row in rows]
