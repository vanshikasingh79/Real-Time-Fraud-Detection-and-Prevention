"""Version one API router."""

from fastapi import APIRouter

from app.api.v1.endpoints.fraud import router as fraud_router


router = APIRouter()
router.include_router(fraud_router, prefix="/fraud")