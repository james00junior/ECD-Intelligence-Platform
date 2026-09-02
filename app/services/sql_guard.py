"""
Safety checks for LLM-generated SQL.

Generated SQL is never executed raw. It must pass the existing
sql_tool.validate_sql SELECT-only layer plus organisation-scope
and table-allowlist checks.
"""

from __future__ import annotations

import re

from app.services.ecd_schema import (
    ALLOWED_TABLES,
    INDIRECT_ORG_TABLES,
    ORG_OWNED_TABLES,
)
from app.tools.sql_tool import validate_sql


_FENCE_RE = re.compile(r"```(?:sql)?\s*([\s\S]*?)```", re.IGNORECASE)
_THINK_RE = re.compile(r"<think>[\s\S]*?</think>", re.IGNORECASE)
_TABLE_RE = re.compile(
    r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
    re.IGNORECASE,
)
_ORG_LITERAL_RE = re.compile(
    r"\borganisation_id\s*=\s*(?![:?])['\"]?\d+",
    re.IGNORECASE,
)
_COMMENT_RE = re.compile(r"(--)|(/\*)")
_UNSUPPORTED_RE = re.compile(r"^\s*UNSUPPORTED\s*$", re.IGNORECASE)


class SQLGuardError(ValueError):
    """Raised when generated SQL fails a safety check."""


def extract_sql(raw: str) -> str:
    """Pull a SQL statement out of model output."""

    if raw is None:
        raise SQLGuardError("Model returned empty SQL.")

    text = str(raw).strip()
    if not text:
        raise SQLGuardError("Model returned empty SQL.")

    text = _THINK_RE.sub("", text).strip()

    fenced = _FENCE_RE.findall(text)
    if fenced:
        text = fenced[0].strip()

    if _UNSUPPORTED_RE.match(text):
        raise SQLGuardError("Question is unsupported for SQL generation.")

    # Keep the first statement if the model added chatter after it.
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith(("here is", "sure,", "sql:")):
            continue
        lines.append(line)
    text = "\n".join(lines).strip()

    if ";" in text.rstrip(";"):
        text = text.split(";", 1)[0].strip()

    return text.strip().rstrip(";").strip()


def referenced_tables(sql: str) -> set[str]:
    return {match.group(1).lower() for match in _TABLE_RE.finditer(sql)}


def requires_organisation_filter(sql: str) -> bool:
    tables = referenced_tables(sql)
    return bool(
        tables & ORG_OWNED_TABLES or tables & set(INDIRECT_ORG_TABLES)
    )


def validate_generated_sql(
    sql: str,
    *,
    organisation_id: int | None,
) -> str:
    """
    Validate generated SQL before execution.

    Returns the cleaned SELECT statement. Raises SQLGuardError on failure.
    """

    cleaned = extract_sql(sql)

    if _COMMENT_RE.search(cleaned):
        raise SQLGuardError("SQL comments are not allowed in generated queries.")

    try:
        validate_sql(cleaned)
    except ValueError as exc:
        raise SQLGuardError(str(exc)) from exc

    tables = referenced_tables(cleaned)
    unknown = tables - ALLOWED_TABLES
    if unknown:
        raise SQLGuardError(
            "Generated SQL references disallowed tables: "
            + ", ".join(sorted(unknown))
        )

    if _ORG_LITERAL_RE.search(cleaned):
        raise SQLGuardError(
            "organisation_id must be the bind parameter :organisation_id, "
            "not a literal value."
        )

    needs_org = requires_organisation_filter(cleaned)
    has_org_param = ":organisation_id" in cleaned

    if organisation_id is not None and needs_org and not has_org_param:
        raise SQLGuardError(
            "Generated SQL must filter organisation-owned tables with "
            "organisation_id = :organisation_id."
        )

    if organisation_id is None and has_org_param:
        raise SQLGuardError(
            "Generated SQL binds :organisation_id but no organisation "
            "scope was provided."
        )

    return cleaned


def sql_parameters(
    sql: str,
    organisation_id: int | None,
) -> dict[str, int]:
    """Bind parameters for a validated statement."""

    if organisation_id is not None and ":organisation_id" in sql:
        return {"organisation_id": organisation_id}
    return {}


__all__ = [
    "SQLGuardError",
    "extract_sql",
    "referenced_tables",
    "requires_organisation_filter",
    "sql_parameters",
    "validate_generated_sql",
]
