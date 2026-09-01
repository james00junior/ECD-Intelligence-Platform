from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


def organisation_exists(
    db: Session,
    organisation_id: int,
) -> bool:
    """
    Check whether an organisation exists.

    The caller owns the database session lifecycle.
    """

    query = text(
        """
        SELECT 1
        FROM organisations
        WHERE id = :organisation_id
        LIMIT 1
        """
    )

    result = db.execute(
        query,
        {
            "organisation_id": organisation_id,
        },
    ).first()

    return result is not None


def get_organisation(
    db: Session,
    organisation_id: int,
) -> dict | None:
    """
    Return an organisation by ID.

    Returns None when the organisation does not exist.
    """

    query = text(
        """
        SELECT
            id,
            name,
            country
        FROM organisations
        WHERE id = :organisation_id
        LIMIT 1
        """
    )

    row = db.execute(
        query,
        {
            "organisation_id": organisation_id,
        },
    ).mappings().first()

    if row is None:
        return None

    return {
        "id": row["id"],
        "name": row["name"],
        "country": row["country"],
    }