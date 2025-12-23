import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, status, Body, Depends, HTTPException
from src.schema.response.storage import NewBucket
from src.schema.requests.storage import Bucket
from src.application.manager import StorageManage
from src.database.database import DatabaseEngine
from src.api.deps import get_current_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=NewBucket, status_code=status.HTTP_201_CREATED)
async def create_bucket(bucket_data: Annotated[Bucket, Body()], user_id: str = Depends(get_current_user)):
    try:
        engine = DatabaseEngine()
        bucket = engine.create_bucket(
            bucket_data=bucket_data,
            user_id=uuid.UUID(user_id)
        )
        storage = StorageManage(bucket_name=bucket.id)
        complete = storage.storage.create_bucket(bucket_name=str(bucket.id))
        return NewBucket(accepted=complete)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
