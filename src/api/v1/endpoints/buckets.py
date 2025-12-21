from fastapi import APIRouter, status, Body
from typing import Annotated

from src.schema.response.storage import NewBucket
from src.schema.requests.storage import Bucket

from src.application.manager import StorageManage

router = APIRouter()


@router.post("/", response_model=NewBucket, status_code=status.HTTP_201_CREATED)
async def create_bucket(bucket_data: Annotated[Bucket, Body()]):
    storage = StorageManage(bucket_name=bucket_data.name)
    complete = storage.storage.create_bucket(bucket_name=bucket_data.name)
    return NewBucket(accepted=complete)
