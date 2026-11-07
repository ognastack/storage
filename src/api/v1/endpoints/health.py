from fastapi import APIRouter, status
from config.settings import settings
from src.schema.response.storage import HealthResponse

router = APIRouter()


@router.get(
    "",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Service health check",
    description="Returns service health status, version, and environment details."
)
@router.get(
    "/",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


@router.get(
    "/live",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
    description="Kubernetes/container liveness check indicating the process is running."
)
async def liveness_check():
    return {"status": "live"}


@router.get(
    "/ready",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
    description="Kubernetes/container readiness check indicating the service is ready to accept traffic."
)
async def readiness_check():
    return {"status": "ready"}
