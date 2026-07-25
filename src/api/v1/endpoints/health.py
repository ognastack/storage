from fastapi import APIRouter, status
from config.settings import settings

router = APIRouter()


@router.get("", status_code=status.HTTP_200_OK)
@router.get("/", status_code=status.HTTP_200_OK)
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_check():
    return {"status": "live"}


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    return {"status": "ready"}
