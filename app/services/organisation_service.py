from sqlalchemy import text

from app.database.database import engine


def organisation_exists(organisation_id: int) -> bool:
    """
    Check whether an organisation exists.
    """

    query = text(
        """
        SELECT 1
        FROM organisations
        WHERE id = :organisation_id
        LIMIT 1
        """
    )

    with engine.connect() as connection:
        result = connection.execute(
            query,
            {"organisation_id": organisation_id},
        ).first()

    return result is not None


def get_organisation(organisation_id: int) -> dict | None:
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

    with engine.connect() as connection:
        row = connection.execute(
            query,
            {"organisation_id": organisation_id},
        ).mappings().first()

    if row is None:
        return None

    return {
        "id": row["id"],
        "name": row["name"],
        "country": row["country"],
    }
