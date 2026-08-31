from app.workflows.router import (
    ANALYTICS_ROUTE,
    UNKNOWN_ROUTE,
    route_question,
)


def test_router_routes_franchisee_question_to_analytics():
    route = route_question(
        "How many franchisees are there?"
    )

    assert route == ANALYTICS_ROUTE


def test_router_routes_children_question_to_analytics():
    route = route_question(
        "How many children are enrolled?"
    )

    assert route == ANALYTICS_ROUTE


def test_router_routes_population_question_to_analytics():
    route = route_question(
        "What is the population by province?"
    )

    assert route == ANALYTICS_ROUTE


def test_router_routes_unknown_question_to_unknown():
    route = route_question(
        "What is the weather in Johannesburg?"
    )

    assert route == UNKNOWN_ROUTE


def test_router_rejects_non_string_question():
    route = route_question(
        123
    )

    assert route == UNKNOWN_ROUTE


def test_router_rejects_empty_question():
    route = route_question(
        ""
    )

    assert route == UNKNOWN_ROUTE
