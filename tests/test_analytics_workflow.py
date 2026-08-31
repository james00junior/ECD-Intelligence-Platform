from app.workflows.analytics_workflow import analytics_workflow


def test_workflow_count_franchisees():

    result = analytics_workflow.invoke(
        {
            "question": "How many franchisees are there?"
        }
    )

    assert result["error"] is None
    assert result["intent"] == "count_franchisees"
    assert result["sql_query"] is not None
    assert result["results"]

    assert (
        result["results"][0]["franchisee_count"]
        >= 0
    )

    assert result["answer"] is not None


def test_workflow_active_franchisees():

    result = analytics_workflow.invoke(
        {
            "question": "How many active franchisees are there?"
        }
    )

    assert result["error"] is None
    assert result["intent"] == "active_franchisees"
    assert result["sql_query"] is not None
    assert result["results"]

    assert (
        result["results"][0]["active_franchisee_count"]
        >= 0
    )

    assert result["answer"] is not None


def test_workflow_children():

    result = analytics_workflow.invoke(
        {
            "question": "How many children are enrolled?"
        }
    )

    assert result["error"] is None
    assert result["intent"] == "count_children"
    assert result["sql_query"] is not None
    assert result["results"]

    assert (
        result["results"][0]["child_count"]
        >= 0
    )

    assert result["answer"] is not None


def test_workflow_by_status():

    result = analytics_workflow.invoke(
        {
            "question": "How many franchisees are there by status?"
        }
    )

    assert result["error"] is None
    assert result["intent"] == "franchisees_by_status"
    assert result["results"]

    assert "status" in result["results"][0]
    assert "franchisee_count" in result["results"][0]

    assert result["answer"] is not None


def test_workflow_unknown_question():

    result = analytics_workflow.invoke(
        {
            "question": "What is the weather in Johannesburg?"
        }
    )

    assert (
        result["error"]
        == "No SQL query could be generated for this question."
    )

    assert result["results"] == []


def test_workflow_router_selects_analytics():

    result = analytics_workflow.invoke(
        {
            "question": "How many franchisees are there?"
        }
    )

    assert result["route"] == "analytics"
    assert result["error"] is None


def test_workflow_router_rejects_unknown_question():

    result = analytics_workflow.invoke(
        {
            "question": "What is the weather in Johannesburg?"
        }
    )

    assert result["route"] == "unknown"

    assert (
        result["error"]
        == "No SQL query could be generated for this question."
    )

    assert result["results"] == []



def test_workflow_generates_franchisee_answer():

    result = analytics_workflow.invoke(
        {
            "question": "How many franchisees are there?"
        }
    )

    assert result["error"] is None
    assert result["answer"] is not None
    assert "franchisees" in result["answer"].lower()


def test_workflow_generates_active_franchisee_answer():

    result = analytics_workflow.invoke(
        {
            "question": (
                "How many active franchisees are there?"
            )
        }
    )

    assert result["error"] is None
    assert result["answer"] is not None
    assert "active franchisees" in result["answer"].lower()


def test_workflow_generates_children_answer():

    result = analytics_workflow.invoke(
        {
            "question": "How many children are enrolled?"
        }
    )

    assert result["error"] is None
    assert result["answer"] is not None
    assert "children" in result["answer"].lower()


def test_workflow_generates_grouped_answer():

    result = analytics_workflow.invoke(
        {
            "question": (
                "How many franchisees are there "
                "by province?"
            )
        }
    )

    assert result["error"] is None
    assert result["answer"] is not None
    assert "province" in result["answer"].lower()


def test_workflow_children_by_province():

    result = analytics_workflow.invoke(
        {
            "question": (
                "How many enrolled children are there by province?"
            )
        }
    )

    assert result["error"] is None
    assert result["intent"] == "children_by_province"
    assert result["sql_query"] is not None
    assert result["results"]
    assert "province" in result["results"][0]
    assert "child_count" in result["results"][0]
    assert result["answer"] is not None


def test_workflow_unknown_question_has_complete_state():

    result = analytics_workflow.invoke(
        {
            "question": (
                "What is the weather in Johannesburg?"
            )
        }
    )

    assert (
        result["error"]
        == "No SQL query could be generated "
        "for this question."
    )

    assert result["results"] == []

    assert result["answer"] is None




