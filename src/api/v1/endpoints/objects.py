import logging
import uuid
from typing import Annotated
from fastapi import File, APIRouter, UploadFile, status, HTTPException, Depends, Path
from src.application.manager import StorageManager
from src.schema.response.storage import FileAccepted, MainResponse
from src.api.deps import get_current_user

router = APIRouter()


@router.post("/{bucket_name}", response_model=FileAccepted, status_code=status.HTTP_201_CREATED)
async def upload_file(
        file: Annotated[UploadFile, File()],
        bucket_name: Annotated[str, Path()],
        user_id: uuid.UUID = Depends(get_current_user)
):
    logging.info(f"Uploading object {file.filename}")
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
