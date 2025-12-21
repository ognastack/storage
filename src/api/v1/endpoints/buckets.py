from fastapi import APIRouter, status, Body, Depends
from typing import Annotated

from src.schema.response.storage import NewBucket
from src.schema.requests.storage import Bucket

from src.application.S3 import S3StorageService

router = APIRouter()


@router.post("/", response_model=NewBucket, status_code=status.HTTP_201_CREATED)
async def create_bucket(bucket_data: Annotated[Bucket, Body()]):
    storage = S3StorageService(
        endpoint_url="http://localhost:9000",  # Example: MinIO endpoint
        access_key="MfXp3q4DobACNTw6xYOL",
        secret_key="xz2GJUyML5kcKqbWCPlrviANOdmE9ZRgpTehsj10",
        bucket_name=bucket_data.name
    )

    complete = storage.create_bucket(bucket_name=bucket_data.name)
    return NewBucket(accepted=complete)
