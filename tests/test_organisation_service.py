from app.services.organisation_service import (
    get_organisation,
    organisation_exists,
)


def test_organisation_exists():
    assert organisation_exists(1) is True


def test_nonexistent_organisation_does_not_exist():
    assert organisation_exists(999999) is False


def test_get_organisation():
    organisation = get_organisation(1)

    assert organisation is not None
    assert organisation["id"] == 1
    assert organisation["name"]
    assert organisation["country"]


def test_get_nonexistent_organisation():
    organisation = get_organisation(999999)

    assert organisation is None
