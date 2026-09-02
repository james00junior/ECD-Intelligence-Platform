"""
Read-only ECD schema catalog used by schema-aware text-to-SQL.

The LLM receives table/column names and join hints only. Database
credentials and connection strings are never included.
"""

from __future__ import annotations


ORG_OWNED_TABLES: frozenset[str] = frozenset(
    {
        "franchisees",
        "children",
        "coaches",
        "documents",
        "document_chunks",
        "knowledge_sources",
    }
)

# These tables have no organisation_id column. Scope them by joining
# an organisation-owned parent table and filtering that parent.
INDIRECT_ORG_TABLES: dict[str, str] = {
    "attendance": "children",
    "monthly_metrics": "franchisees",
}

ALLOWED_TABLES: frozenset[str] = frozenset(
    {
        "organisations",
        "franchisees",
        "children",
        "coaches",
        "attendance",
        "monthly_metrics",
        "provinces",
        "municipalities",
        "local_municipalities",
        "main_places",
        "sub_places",
        "small_areas",
        "population_snapshots",
    }
)

SCHEMA_CATALOG = """
PostgreSQL schema for ECD operational analytics (read-only).

organisations(
  id integer primary key,
  name varchar,
  country varchar
)

coaches(
  id integer primary key,
  organisation_id integer not null,  -- REQUIRED tenant filter
  name varchar
)

franchisees(
  id integer primary key,
  organisation_id integer not null,  -- REQUIRED tenant filter
  small_area_id integer not null,
  coach_id integer not null,
  name varchar,
  status varchar,                    -- values include 'ACTIVE', 'INACTIVE'
  start_date date,
  inactive_date date,
  capacity integer
)

children(
  id integer primary key,
  organisation_id integer not null,  -- REQUIRED tenant filter
  franchisee_id integer not null,
  residential_small_area_id integer not null,
  date_of_birth date,
  enrolment_date date,
  status varchar                     -- values include 'ENROLLED'
)

attendance(
  id integer primary key,
  child_id integer not null,         -- join children to apply organisation_id
  attendance_date date,
  attended integer                   -- 1 = present, 0 = absent
)

monthly_metrics(
  id integer primary key,
  franchisee_id integer not null,    -- join franchisees to apply organisation_id
  month date,
  enrolled_children integer,
  attendance_rate float,
  capacity_utilisation float,
  new_enrolments integer,
  exits integer
)

provinces(id integer primary key, name varchar)
municipalities(id integer primary key, province_id integer, name varchar, municipality_type varchar)
local_municipalities(id integer primary key, municipality_id integer, name varchar)
main_places(id integer primary key, local_municipality_id integer, name varchar)
sub_places(id integer primary key, main_place_id integer, name varchar)
small_areas(id integer primary key, sub_place_id integer, name varchar, census_code varchar, area_km2 float)

population_snapshots(
  id integer primary key,
  small_area_id integer not null,
  census_year integer,
  population_total integer,
  children_0_4 integer,
  children_5_9 integer,
  households integer
)

Geography join path (franchisee location):
  franchisees f
  JOIN small_areas sa ON sa.id = f.small_area_id
  JOIN sub_places sp ON sp.id = sa.sub_place_id
  JOIN main_places mp ON mp.id = sp.main_place_id
  JOIN local_municipalities lm ON lm.id = mp.local_municipality_id
  JOIN municipalities m ON m.id = lm.municipality_id
  JOIN provinces p ON p.id = m.province_id

Child residential geography: join from children.residential_small_area_id
using the same small_areas -> ... -> provinces path.

Organisation-owned tables MUST be filtered with:
  <alias>.organisation_id = :organisation_id
Use the bind parameter :organisation_id. Never embed a numeric organisation id.
For attendance, join children and filter children.organisation_id.
For monthly_metrics, join franchisees and filter franchisees.organisation_id.
""".strip()


SQL_GENERATION_RULES = """
Return one PostgreSQL SELECT statement that answers the question.
Rules:
- SELECT only. Never INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, GRANT, REVOKE, COPY, or SELECT INTO.
- Single statement. No semicolons except an optional trailing one.
- No SQL comments.
- Use only tables listed in the schema catalog.
- When organisation_id is provided and the query touches organisation-owned or
  indirectly owned tables, include organisation_id = :organisation_id.
- Prefer aggregates (COUNT, SUM, AVG) and GROUP BY for "how many" / "by X" questions.
- Limit row listings to 100 rows.
- If the question cannot be answered from this schema, return exactly: UNSUPPORTED
- Output the SQL only. No markdown fences and no commentary.
""".strip()


def schema_prompt(organisation_id: int | None) -> str:
    org_line = (
        f"The request is scoped to organisation_id = {organisation_id}. "
        "You MUST use the bind parameter :organisation_id; do not inline the number."
        if organisation_id is not None
        else "No organisation scope was supplied. Do not invent an organisation_id filter."
    )
    return f"{SCHEMA_CATALOG}\n\n{SQL_GENERATION_RULES}\n\n{org_line}"


__all__ = [
    "ALLOWED_TABLES",
    "INDIRECT_ORG_TABLES",
    "ORG_OWNED_TABLES",
    "SCHEMA_CATALOG",
    "SQL_GENERATION_RULES",
    "schema_prompt",
]
