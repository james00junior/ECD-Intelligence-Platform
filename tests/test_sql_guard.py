import pytest

from app.services.sql_guard import (
    SQLGuardError,
    extract_sql,
    validate_generated_sql,
)


def test_extract_sql_strips_markdown_fence():
    raw = """```sql
SELECT COUNT(*) AS franchisee_count
FROM franchisees
WHERE organisation_id = :organisation_id
```"""
    sql = extract_sql(raw)
    assert sql.upper().startswith("SELECT")
    assert "organisation_id = :organisation_id" in sql


def test_valid_select_with_org_filter_passes():
    sql = validate_generated_sql(
        """
        SELECT COUNT(*) AS franchisee_count
        FROM franchisees
        WHERE organisation_id = :organisation_id
        """,
        organisation_id=1,
    )
    assert sql.upper().startswith("SELECT")


def test_reject_drop_statement():
    with pytest.raises(SQLGuardError, match="Only SELECT"):
        validate_generated_sql(
            "DROP TABLE franchisees",
            organisation_id=1,
        )


def test_reject_insert_statement():
    with pytest.raises(SQLGuardError, match="Only SELECT"):
        validate_generated_sql(
            "INSERT INTO franchisees (name) VALUES ('x')",
            organisation_id=1,
        )


def test_reject_org_owned_query_without_org_filter():
    with pytest.raises(SQLGuardError, match="organisation_id"):
        validate_generated_sql(
            "SELECT COUNT(*) AS franchisee_count FROM franchisees",
            organisation_id=1,
        )


def test_reject_literal_organisation_id():
    with pytest.raises(SQLGuardError, match="bind parameter"):
        validate_generated_sql(
            "SELECT COUNT(*) FROM franchisees WHERE organisation_id = 1",
            organisation_id=1,
        )


def test_reject_disallowed_table():
    with pytest.raises(SQLGuardError, match="disallowed tables"):
        validate_generated_sql(
            "SELECT * FROM pg_shadow",
            organisation_id=None,
        )


def test_reject_sql_comments():
    with pytest.raises(SQLGuardError, match="comments"):
        validate_generated_sql(
            "SELECT COUNT(*) FROM franchisees -- DROP TABLE franchisees",
            organisation_id=1,
        )


def test_extract_sql_strips_think_tags():
    raw = """<think>planning</think>
SELECT COUNT(*) AS franchisee_count
FROM franchisees
WHERE organisation_id = :organisation_id
"""
    sql = extract_sql(raw)
    assert "think" not in sql.lower()
    assert sql.upper().startswith("SELECT")
