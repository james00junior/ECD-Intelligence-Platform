from fastapi import APIRouter

from app.api.v1.agent import router as agent_router
from app.api.v1.health import router as health_router
from app.api.v1.organisations import router as organisations_router


router = APIRouter(
    prefix="/api/v1",
)


router.include_router(
    health_router,
)

router.include_router(
    agent_router,
)

router.include_router(
    organisations_router,
)