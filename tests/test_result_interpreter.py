from app.services.result_interpreter import interpret_results, render_rows


def test_render_rows_single_metric():
    answer = render_rows(
        "How many franchisees?",
        [{"franchisee_count": 60}],
    )
    assert "60" in answer
    assert "franchisee count" in answer.lower()


def test_render_rows_grouped():
    answer = render_rows(
        "Franchisees by status",
        [
            {"status": "ACTIVE", "franchisee_count": 42},
            {"status": "INACTIVE", "franchisee_count": 18},
        ],
    )
    assert "ACTIVE" in answer
    assert "42" in answer


def test_interpret_canned_intent_keeps_template():
    answer = interpret_results(
        "How many franchisees are there?",
        [{"franchisee_count": 60}],
        intent="count_franchisees",
        sql_source="canned",
        use_llm=False,
    )
    assert answer == "There are currently 60 franchisees."


def test_interpret_generated_sql_uses_renderer():
    answer = interpret_results(
        "How many franchisees does each coach manage?",
        [{"coach": "Amina", "franchisee_count": 4}],
        intent="generated_sql",
        sql_source="generated",
        use_llm=False,
    )
    assert "Amina" in answer
    assert "4" in answer
