from fastapi import APIRouter

from src.api.v1.endpoints import objects, buckets

api_router = APIRouter()

api_router.include_router(
    objects.router,
    prefix="/objects",
    tags=["objects"]
)

api_router.include_router(
    buckets.router,
    prefix="/buckets",
    tags=["buckets"]
)
