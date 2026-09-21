"""Version one API router."""

from fastapi import APIRouter

from app.api.v1.endpoints.fraud import router as fraud_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.metrics import router as metrics_router


router = APIRouter()
router.include_router(health_router)
router.include_router(metrics_router)
router.include_router(fraud_router)
router.include_router(fraud_router, prefix="/fraud")