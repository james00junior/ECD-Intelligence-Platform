from fastapi import APIRouter

from app.api.schemas import HealthResponse


router = APIRouter(
    prefix="/health",
    tags=["health"],
)


@router.get(
    "",
    response_model=HealthResponse,
)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version="0.3.0",
    )