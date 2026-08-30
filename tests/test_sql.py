import pytest

from app.tools.sql_tool import execute_sql, validate_sql


def test_validate_select():
    """A normal SELECT query should pass validation."""

    query = "SELECT * FROM franchisees"

    validate_sql(query)


def test_reject_delete():
    """DELETE statements must be rejected."""

    with pytest.raises(
        ValueError,
        match="Only SELECT statements are allowed",
    ):
        validate_sql(
            "DELETE FROM franchisees"
        )


def test_reject_insert():
    """INSERT statements must be rejected."""

    with pytest.raises(
        ValueError,
        match="Only SELECT statements are allowed",
    ):
        validate_sql(
            "INSERT INTO franchisees VALUES (1)"
        )


def test_execute_select():
    """A valid SELECT query should execute against PostgreSQL."""

    rows = execute_sql(
        """
        SELECT
            id,
            name,
            status,
            capacity
        FROM franchisees
        ORDER BY id
        LIMIT 5
        """
    )

    assert isinstance(rows, list)

    if rows:
        assert isinstance(rows[0], dict)

        assert "id" in rows[0]
        assert "name" in rows[0]
        assert "status" in rows[0]
        assert "capacity" in rows[0]