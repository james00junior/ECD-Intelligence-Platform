from app.services.text_to_sql import generate_select
from app.tools import sql_tool


VALID_SQL = """
SELECT COUNT(*) AS franchisee_count
FROM franchisees
WHERE organisation_id = :organisation_id
"""

DROP_SQL = "DROP TABLE franchisees"
INSERT_SQL = "INSERT INTO franchisees (name) VALUES ('x')"


def test_generate_select_accepts_valid_select():
    generated = generate_select(
        "How many franchisees are there?",
        organisation_id=1,
        complete=lambda prompt: VALID_SQL,
        max_repairs=0,
    )
    assert generated is not None
    assert generated.sql.upper().startswith("SELECT")
    assert generated.parameters == {"organisation_id": 1}
    assert generated.source == "generated"
    assert generated.repaired is False


def test_generate_select_rejects_drop_without_repair():
    generated = generate_select(
        "How many franchisees are there?",
        organisation_id=1,
        complete=lambda prompt: DROP_SQL,
        max_repairs=0,
    )
    assert generated is None


def test_generate_select_rejects_insert_without_repair():
    generated = generate_select(
        "How many franchisees are there?",
        organisation_id=1,
        complete=lambda prompt: INSERT_SQL,
        max_repairs=0,
    )
    assert generated is None


def test_generate_select_requires_org_filter():
    generated = generate_select(
        "How many franchisees are there?",
        organisation_id=1,
        complete=lambda prompt: "SELECT COUNT(*) FROM franchisees",
        max_repairs=0,
    )
    assert generated is None


def test_repair_loop_recovers_from_invalid_sql():
    calls = {"n": 0}

    def complete(prompt: str) -> str:
        calls["n"] += 1
        if calls["n"] == 1:
            return DROP_SQL
        assert "DROP" in prompt or "validation" in prompt.lower() or "failed" in prompt.lower()
        return VALID_SQL

    generated = generate_select(
        "How many franchisees are there?",
        organisation_id=1,
        complete=complete,
        max_repairs=2,
    )
    assert generated is not None
    assert generated.repaired is True
    assert generated.attempts == 2
    assert generated.sql.upper().startswith("SELECT")
    assert generated.parameters["organisation_id"] == 1


def test_generated_sql_is_validated_before_execute(monkeypatch):
    executed = {"called": False}

    def fake_execute(query, parameters=None):
        executed["called"] = True
        return [{"franchisee_count": 1}]

    monkeypatch.setattr(sql_tool, "execute_sql", fake_execute)

    generated = generate_select(
        "How many franchisees are there?",
        organisation_id=1,
        complete=lambda prompt: DROP_SQL,
        max_repairs=0,
    )
    assert generated is None
    assert executed["called"] is False


def test_generate_select_returns_none_when_completer_raises():
    def complete(prompt: str) -> str:
        raise RuntimeError("ollama down")

    generated = generate_select(
        "How many franchisees are there?",
        organisation_id=1,
        complete=complete,
    )
    assert generated is None
