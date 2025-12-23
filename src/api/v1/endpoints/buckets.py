import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, status, Body, Depends, HTTPException
from src.schema.response.storage import NewBucket
from src.schema.requests.storage import Bucket
from src.application.manager import StorageManager

from src.api.deps import get_current_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=NewBucket, status_code=status.HTTP_201_CREATED)
async def create_bucket(bucket_data: Annotated[Bucket, Body()], user_id: uuid.UUID = Depends(get_current_user)):
    manager = StorageManager(bucket_name=bucket_data.name)

    return manager.create_bucket(
        bucket_data=bucket_data,
        current_user=user_id
    )
