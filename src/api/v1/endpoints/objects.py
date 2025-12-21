from fastapi import APIRouter, UploadFile, status, Body, HTTPException
from typing import Annotated
from src.application.S3 import S3StorageService
from src.schema.response.storage import FileAccepted, MainResponse
from src.schema.requests.storage import NewObject

router = APIRouter()


@router.post("/{bucket_name}", response_model=FileAccepted, status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile, bucket_name: str):
    storage = S3StorageService(
        endpoint_url="http://localhost:9000",  # Example: MinIO endpoint
        access_key="MfXp3q4DobACNTw6xYOL",
        secret_key="xz2GJUyML5kcKqbWCPlrviANOdmE9ZRgpTehsj10",
        bucket_name=bucket_name
    )
    try:
        # Use the object_name from bucket_data or fallback to original filename
        object_name = file.filename

        # Switch to the specified bucket if different
        original_bucket = storage.bucket_name
        storage.bucket_name = bucket_name

        # Ensure the bucket exists
        storage.create_bucket(bucket_name)

        # Upload the file using upload_fileobj (works with FastAPI UploadFile)
        success = storage.upload_fileobj(
            file.file,
            object_name
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file"
            )

        # Generate presigned URL (optional)
        url = storage.get_presigned_url(object_name)

        # Restore original bucket
        storage.bucket_name = original_bucket

        return FileAccepted(
            success=success,
            url=url
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{bucket_name}/{file_name}", status_code=status.HTTP_200_OK, response_model=MainResponse)
async def delete_file(bucket_name: str, file_name: str):
    storage = S3StorageService(
        endpoint_url="http://localhost:9000",  # Example: MinIO endpoint
        access_key="MfXp3q4DobACNTw6xYOL",
        secret_key="xz2GJUyML5kcKqbWCPlrviANOdmE9ZRgpTehsj10",
        bucket_name=bucket_name
    )

    try:
        success = storage.delete_file(object_name=file_name)
        return MainResponse(accepted=success)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
