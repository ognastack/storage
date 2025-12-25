import logging
import uuid
from typing import Annotated
from fastapi import File, APIRouter, UploadFile, status, Depends, Path, Body

from src.schema.response.storage import NewBucket
from src.schema.requests.storage import Bucket

from src.application.manager import StorageManager
from src.schema.response.storage import FileAccepted, MainResponse
from fastapi.responses import FileResponse

from src.api.deps import get_current_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=NewBucket, status_code=status.HTTP_201_CREATED)
async def create_bucket(bucket_data: Annotated[Bucket, Body()], user_id: uuid.UUID = Depends(get_current_user)):
    manager = StorageManager(bucket_name=bucket_data.name)

    return manager.create_bucket(
        bucket_data=bucket_data,
        current_user=user_id
    )


@router.get("", status_code=status.HTTP_200_OK)
async def list_buckets(user_id: uuid.UUID = Depends(get_current_user)):
    manager = StorageManager(bucket_name='')
    return manager.get_buckets(current_user=user_id)


@router.post("/{bucket_name}", response_model=FileAccepted, status_code=status.HTTP_201_CREATED)
async def upload_file(
        file: Annotated[UploadFile, File()],
        bucket_name: Annotated[str, Path()],
        user_id: uuid.UUID = Depends(get_current_user)
):
    manager = StorageManager(bucket_name=bucket_name)

    url = manager.upload_file(
        file=file,
        current_user=user_id
    )
    logging.info(f"Object {file.filename} finalized")

    return FileAccepted(
        success=True,
        url=url
    )


@router.get("/{bucket_name}", status_code=status.HTTP_200_OK)
async def list_files(bucket_name: Annotated[str, Path()], user_id: uuid.UUID = Depends(get_current_user)):
    manager = StorageManager(bucket_name=bucket_name)
    return manager.get_files(current_user=user_id)


@router.delete("/{bucket_name}/{file_name}", status_code=status.HTTP_201_CREATED, response_model=MainResponse)
async def delete_file(
        bucket_name: str,
        file_name: str,
        user_id: uuid.UUID = Depends(get_current_user)
):
    deletion = StorageManager(bucket_name=bucket_name).delete_file(
        file_name=file_name,
        current_user=user_id
    )
    return MainResponse(accepted=deletion)


@router.get("/{bucket_name}/{file_name}", status_code=status.HTTP_200_OK)
async def get_file(
        bucket_name: str,
        file_name: str,
        user_id: uuid.UUID = Depends(get_current_user)
):
    file_path, file_name = StorageManager(bucket_name=bucket_name).get_file(
        file_name=file_name,
        current_user=user_id
    )
    return FileResponse(
        path=file_path,
        filename=file_name
    )
