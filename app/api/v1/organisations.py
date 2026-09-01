from fastapi import APIRouter
from sqlalchemy import text

from app.api.schemas import OrganisationResponse
from app.database.database import engine


router = APIRouter(
    prefix="/organisations",
    tags=["organisations"],
)


@router.get(
    "",
    response_model=list[OrganisationResponse],
)
def list_organisations() -> list[OrganisationResponse]:

    query = text(
        """
        SELECT
            id,
            name,
            country
        FROM organisations
        ORDER BY id
        """
    )

    with engine.connect() as connection:
        rows = connection.execute(query).mappings().all()

    return [
        OrganisationResponse(
            id=row["id"],
            name=row["name"],
            country=row["country"],
        )
        for row in rows
    ]