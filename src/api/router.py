from fastapi import APIRouter
from config.settings import settings
from src.api.v1.endpoints import buckets

api_router = APIRouter()

api_router.include_router(
    buckets.router,
    prefix=f"{settings.API_V1_STR}/buckets",
    tags=["buckets"]
)
