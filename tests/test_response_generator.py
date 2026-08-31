from app.agents.response_generator import generate_response


def test_generate_franchisee_count_response():

    answer = generate_response(
        intent="count_franchisees",
        results=[
            {
                "franchisee_count": 60
            }
        ],
    )

    assert answer == "There are currently 60 franchisees."


def test_generate_active_franchisee_response():

    answer = generate_response(
        intent="active_franchisees",
        results=[
            {
                "active_franchisee_count": 42
            }
        ],
    )

    assert answer == (
        "There are currently 42 active franchisees."
    )


def test_generate_children_response():

    answer = generate_response(
        intent="count_children",
        results=[
            {
                "child_count": 2260
            }
        ],
    )

    assert answer == (
        "There are currently 2,260 enrolled children."
    )


def test_generate_franchisees_by_status_response():

    answer = generate_response(
        intent="franchisees_by_status",
        results=[
            {
                "status": "ACTIVE",
                "franchisee_count": 42,
            },
            {
                "status": "INACTIVE",
                "franchisee_count": 18,
            },
        ],
    )

    assert "Franchisees by status:" in answer
    assert "ACTIVE: 42" in answer
    assert "INACTIVE: 18" in answer


def test_generate_franchisees_by_province_response():

    answer = generate_response(
        intent="franchisees_by_province",
        results=[
            {
                "province": "Gauteng",
                "franchisee_count": 25,
            },
            {
                "province": "Western Cape",
                "franchisee_count": 17,
            },
        ],
    )

    assert "Franchisees by province:" in answer
    assert "Gauteng: 25" in answer
    assert "Western Cape: 17" in answer


def test_generate_population_response():

    answer = generate_response(
        intent="population_by_province",
        results=[
            {
                "province": "Gauteng",
                "population": 1000000,
            }
        ],
    )

    assert "Population by province:" in answer
    assert "Gauteng: 1,000,000" in answer


def test_generate_empty_response():

    answer = generate_response(
        intent="count_franchisees",
        results=[],
    )

    assert answer == "No results were found."


def test_generate_unknown_intent_response():

    answer = generate_response(
        intent="unknown_intent",
        results=[
            {
                "value": 1
            }
        ],
    )

    assert answer == (
        "The query was completed successfully."
    )