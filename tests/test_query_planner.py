from app.services.query_planner import (
    AnalyticsPlan,
    build_query_plan,
    plan_to_dict,
)


def test_plan_count_franchisees():
    plan = build_query_plan(
        "How many franchisees are there?"
    )

    assert isinstance(plan, AnalyticsPlan)
    assert plan.intent == "count_franchisees"
    assert plan.entity == "franchisees"
    assert plan.measure == "count"
    assert plan.dimension is None



def test_plan_active_franchisees():
    plan = build_query_plan(
        "How many active franchisees are there?"
    )

    assert plan is not None
    assert plan.intent == "active_franchisees"
    assert plan.entity == "franchisees"
    assert plan.measure == "count"
    assert plan.dimension == "active"



def test_plan_children():
    plan = build_query_plan(
        "How many children are enrolled?"
    )

    assert plan is not None
    assert plan.intent == "count_children"
    assert plan.entity == "children"
    assert plan.measure == "count"
    assert plan.dimension == "enrolled"



def test_plan_by_status():
    plan = build_query_plan(
        "How many franchisees are there by status?"
    )

    assert plan is not None
    assert plan.intent == "franchisees_by_status"
    assert plan.dimension == "status"



def test_plan_by_province():
    plan = build_query_plan(
        "How many franchisees are there by province?"
    )

    assert plan is not None
    assert plan.intent == "franchisees_by_province"
    assert plan.dimension == "province"



def test_plan_main_place():
    plan = build_query_plan(
        "How many franchisees are there by main place?"
    )

    assert plan is not None
    assert plan.intent == "franchisees_by_main_place"
    assert plan.dimension == "main_place"



def test_plan_children_by_province():
    plan = build_query_plan(
        "How many enrolled children are there by province?"
    )

    assert plan is not None
    assert plan.intent == "children_by_province"
    assert plan.entity == "children"
    assert plan.dimension == "province"


def test_plan_population_by_province():
    plan = build_query_plan(
        "What is the population by province?"
    )

    assert plan is not None
    assert plan.intent == "population_by_province"
    assert plan.entity == "population"
    assert plan.measure == "sum"
    assert plan.dimension == "province"



def test_plan_unknown_question():
    plan = build_query_plan(
        "What is the weather in Johannesburg?"
    )

    assert plan is None



def test_plan_empty_question():
    plan = build_query_plan("")

    assert plan is None




def test_plan_non_string():
    plan = build_query_plan(None)

    assert plan is None




def test_plan_to_dict():
    plan = build_query_plan(
        "How many franchisees are there by province?"
    )

    result = plan_to_dict(plan)

    assert result == {
        "intent": "franchisees_by_province",
        "entity": "franchisees",
        "measure": "count",
        "dimension": "province",
    }




def test_plan_to_dict_none():

    assert plan_to_dict(None) is None
