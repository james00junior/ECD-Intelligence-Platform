from app.database.database import SessionLocal
from app.services.organisation_service import (
    get_organisation,
    organisation_exists,
)


def test_organisation_exists():
    with SessionLocal() as db:
        assert organisation_exists(db, 1) is True


def test_nonexistent_organisation_does_not_exist():
    with SessionLocal() as db:
        assert organisation_exists(db, 999999) is False


def test_get_organisation():
    with SessionLocal() as db:
        organisation = get_organisation(db, 1)

        assert organisation is not None
        assert organisation["id"] == 1
        assert organisation["name"]
        assert organisation["country"]


def test_get_nonexistent_organisation():
    with SessionLocal() as db:
        organisation = get_organisation(db, 999999)

        assert organisation is None