
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

    Phase 1 policy:
    - Query must not be empty.
    - Only SELECT statements are allowed.
    - Multiple SQL statements are rejected.
    - Common write/DDL operations are rejected.

    This is intentionally a basic safety layer.
    A proper SQL parser and database-level read-only
    permissions will be added in later phases.
    """

    if not query or not query.strip():
        raise ValueError("SQL query cannot be empty.")

    normalized_query = query.strip().upper()

    # Only SELECT queries are permitted.
    if not normalized_query.startswith("SELECT"):
        raise ValueError(
            "Only SELECT statements are allowed."
        )

    # Reject multiple SQL statements.
    if ";" in normalized_query.rstrip(";"):
        raise ValueError(
            "Multiple SQL statements are not allowed."
        )

    # Basic protection against write/DDL operations.
    tokens = normalized_query.replace(
        "(", " "
    ).replace(
        ")", " "
    ).replace(
        ",", " "
    ).split()

    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in tokens:
            raise ValueError(
                f"Forbidden SQL keyword detected: {keyword}"
            )


def execute_sql(query: str) -> list[dict[str, Any]]:
    """
    Execute a validated read-only SQL query.

    Returns:
        A list of dictionaries where each dictionary represents
        one database row.
    """

    validate_sql(query)

    with engine.connect() as connection:

        result: Result = connection.execute(
            text(query)
        )

        columns = result.keys()

        rows = [
            dict(zip(columns, row))
            for row in result.fetchall()
        ]

    return rows
