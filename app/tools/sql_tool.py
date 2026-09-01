from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Result

from app.database.database import engine


FORBIDDEN_KEYWORDS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "GRANT",
    "REVOKE",
}


def validate_sql(query: str) -> None:
    """
    Validate a SQL query before execution.

    Phase 2 policy:
    - Query must not be empty.
    - Only SELECT statements are allowed.
    - Multiple SQL statements are rejected.
    - Common write/DDL operations are rejected.
    """

    if not query or not query.strip():
        raise ValueError("SQL query cannot be empty.")

    normalized_query = query.strip().upper()

    if not normalized_query.startswith("SELECT"):
        raise ValueError(
            "Only SELECT statements are allowed."
        )

    if ";" in normalized_query.rstrip(";"):
        raise ValueError(
            "Multiple SQL statements are not allowed."
        )

    tokens = (
        normalized_query
        .replace("(", " ")
        .replace(")", " ")
        .replace(",", " ")
        .split()
    )

    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in tokens:
            raise ValueError(
                f"Forbidden SQL keyword detected: {keyword}"
            )


def execute_sql(
    query: str,
    parameters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Execute a validated read-only SQL query.

    Parameters are passed separately from the SQL text so that
    organisation identifiers and future user-supplied values are
    parameterised rather than interpolated into SQL.
    """

    validate_sql(query)

    with engine.connect() as connection:
        result: Result = connection.execute(
            text(query),
            parameters or {},
        )

        columns = result.keys()

        rows = [
            dict(zip(columns, row))
            for row in result.fetchall()
        ]

    return rows