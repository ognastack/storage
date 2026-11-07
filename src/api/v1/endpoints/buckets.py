import logging
import os
import uuid
from typing import Annotated
from fastapi import File, APIRouter, UploadFile, status, Depends, Path, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.background import BackgroundTask

from src.schema.response.storage import NewBucket, FileAccepted, MainResponse, ErrorResponse
from src.schema.requests.storage import Bucket, FileObject

from src.application.manager import StorageManager
from fastapi.responses import FileResponse

from src.api.deps import get_current_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer(description="Bearer JWT token issued by GoTrue / Auth service")


def _cleanup_temp_file(path: str) -> None:
    """Remove temporary downloaded file after response finishes streaming."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError as exc:
        logger.warning(f"Failed to remove temporary file {path}: {exc}")

COMMON_AUTH_RESPONSES = {
    status.HTTP_401_UNAUTHORIZED: {
        "model": ErrorResponse,
        "description": "Missing or invalid JWT bearer token"
    }
}


@router.post(
    "",
    response_model=NewBucket,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new bucket",
    description="Creates a new bucket record in the database and provisions the underlying storage bucket (S3 or Local).",
    responses={
        **COMMON_AUTH_RESPONSES,
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ErrorResponse,
            "description": "Validation error in request payload"
        }
    }
)
async def create_bucket(
        bucket_data: Annotated[Bucket, Body(description="Bucket configuration to create")],
        user_id: uuid.UUID = Depends(get_current_user),
        credentials: HTTPAuthorizationCredentials = Depends(security)
):
    manager = StorageManager(bucket_name=bucket_data.name, user_token=credentials.credentials)

    return manager.create_bucket(
        bucket_data=bucket_data,
        current_user=user_id
    )


@router.get(
    "",
    response_model=list[Bucket],
    status_code=status.HTTP_200_OK,
    summary="List all buckets",
    description="Returns all storage buckets accessible to the authenticated user.",
    responses=COMMON_AUTH_RESPONSES
)
async def list_buckets(
        user_id: uuid.UUID = Depends(get_current_user),
        credentials: HTTPAuthorizationCredentials = Depends(security)
):
    manager = StorageManager(bucket_name='', user_token=credentials.credentials)
    return manager.get_buckets(current_user=user_id)


@router.get(
    "/{bucket_name}",
    response_model=Bucket,
    status_code=status.HTTP_200_OK,
    summary="Get bucket details",
    description="Retrieves metadata for a specific bucket owned by the authenticated user.",
    responses={
        **COMMON_AUTH_RESPONSES,
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Bucket not found"
        }
    }
)
async def get_bucket(
        bucket_name: Annotated[str, Path(description="Name of the target bucket")],
        user_id: uuid.UUID = Depends(get_current_user),
        credentials: HTTPAuthorizationCredentials = Depends(security)
):
    manager = StorageManager(bucket_name=bucket_name, user_token=credentials.credentials)
    return manager.get_bucket(current_user=user_id)


@router.delete(
    "/{bucket_name}",
    response_model=MainResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a bucket",
    description="Deletes the bucket and all of its objects from both the storage backend and the database.",
    responses={
        **COMMON_AUTH_RESPONSES,
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Bucket not found"
        }
    }
)
async def delete_bucket(
        bucket_name: Annotated[str, Path(description="Name of the bucket to delete")],
        user_id: uuid.UUID = Depends(get_current_user),
        credentials: HTTPAuthorizationCredentials = Depends(security)
):
    deletion = StorageManager(bucket_name=bucket_name, user_token=credentials.credentials).delete_bucket(
        current_user=user_id
    )
    return MainResponse(accepted=deletion)


@router.post(
    "/{bucket_name}/files",
    response_model=FileAccepted,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a new file to a bucket",
    description="Uploads a file using multipart/form-data. Uses the uploaded file's filename as the object key and returns a presigned download URL and file ID.",
    responses={
        **COMMON_AUTH_RESPONSES,
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Bucket not found"
        }
    }
)
async def upload_file(
        file: Annotated[UploadFile, File(description="Binary file to upload")],
        bucket_name: Annotated[str, Path(description="Name of the destination bucket")],
        user_id: uuid.UUID = Depends(get_current_user),
        credentials: HTTPAuthorizationCredentials = Depends(security)
):
    manager = StorageManager(bucket_name=bucket_name, user_token=credentials.credentials)

    url, file_id = manager.upload_file(
        file=file,
        current_user=user_id
    )
    logger.info(f"Object {file.filename} finalized")

    return FileAccepted(
        accepted=True,
        url=url,
        file_id=file_id
    )


@router.get(
    "/{bucket_name}/files",
    response_model=list[FileObject],
    status_code=status.HTTP_200_OK,
    summary="List files in a bucket",
    description="Returns metadata for all files stored inside the specified bucket.",
    responses=COMMON_AUTH_RESPONSES
)
async def list_files(
        bucket_name: Annotated[str, Path(description="Name of the bucket")],
        user_id: uuid.UUID = Depends(get_current_user),
        credentials: HTTPAuthorizationCredentials = Depends(security)
):
    manager = StorageManager(bucket_name=bucket_name, user_token=credentials.credentials)
    return manager.get_files(current_user=user_id)


@router.put(
    "/{bucket_name}/files/{file_name}",
    response_model=FileAccepted,
    status_code=status.HTTP_200_OK,
    summary="Upload or replace a file by name",
    description="Uploads or overwrites a file at the specified `{file_name}` key inside the bucket and returns a presigned URL and file ID.",
    responses={
        **COMMON_AUTH_RESPONSES,
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Bucket not found"
        }
    }
)
async def replace_file(
        file: Annotated[UploadFile, File(description="Binary file content to store at file_name")],
        bucket_name: Annotated[str, Path(description="Name of the target bucket")],
        file_name: Annotated[str, Path(description="Target file name / object key in the bucket")],
        user_id: uuid.UUID = Depends(get_current_user),
        credentials: HTTPAuthorizationCredentials = Depends(security)
):
    manager = StorageManager(bucket_name=bucket_name, user_token=credentials.credentials)

    url, file_id = manager.upload_file(
        file=file,
        current_user=user_id,
        file_name=file_name
    )
    logger.info(f"Object {file_name} finalized")

    return FileAccepted(
        accepted=True,
        url=url,
        file_id=file_id
    )


@router.get(
    "/{bucket_name}/files/{file_name}",
    response_class=FileResponse,
    status_code=status.HTTP_200_OK,
    summary="Download a file",
    description="Downloads the specified file from the storage backend and streams it as a file attachment.",
    responses={
        **COMMON_AUTH_RESPONSES,
        status.HTTP_200_OK: {
            "content": {"application/octet-stream": {}},
            "description": "Binary file stream"
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "File or bucket not found"
        }
    }
)
async def get_file(
        bucket_name: Annotated[str, Path(description="Name of the bucket containing the file")],
        file_name: Annotated[str, Path(description="Name of the file to download")],
        user_id: uuid.UUID = Depends(get_current_user),
        credentials: HTTPAuthorizationCredentials = Depends(security)
):
    file_path = StorageManager(bucket_name=bucket_name, user_token=credentials.credentials).get_file(
        file_name=file_name,
        current_user=user_id
    )

    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_name),
        background=BackgroundTask(_cleanup_temp_file, file_path)
    )


@router.delete(
    "/{bucket_name}/files/{file_name}",
    response_model=MainResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a file",
    description="Deletes a file from both the storage backend and the database.",
    responses={
        **COMMON_AUTH_RESPONSES,
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "File not found"
        }
    }
)
async def delete_file(
        bucket_name: Annotated[str, Path(description="Name of the bucket containing the file")],
        file_name: Annotated[str, Path(description="Name of the file to delete")],
        user_id: uuid.UUID = Depends(get_current_user),
        credentials: HTTPAuthorizationCredentials = Depends(security)
):
    deletion = StorageManager(bucket_name=bucket_name, user_token=credentials.credentials).delete_file(
        file_name=file_name,
        current_user=user_id
    )
    return MainResponse(accepted=deletion)
