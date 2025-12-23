import uuid
from fastapi import APIRouter, UploadFile, status, HTTPException, Depends
from src.application.manager import StorageManage
from src.schema.response.storage import FileAccepted, MainResponse
from src.database.database import DatabaseEngine
from src.api.deps import get_current_user

router = APIRouter()


@router.post("/{bucket_name}", response_model=FileAccepted, status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile, bucket_name: str, user_id: str = Depends(get_current_user)):
    try:

        engine = DatabaseEngine()
        bucket = engine.get_bucket_by_id_user(
            bucket_name=bucket_name,
            owner_id=uuid.UUID(user_id)
        )

        if bucket is None:
            raise Exception('Bucket not found')

        object_name = file.filename

        storage = StorageManage(bucket_name=str(bucket.id)).storage

        storage.create_bucket(bucket_name)

        success = storage.upload_fileobj(
            file.file,
            object_name
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file"
            )

        return FileAccepted(
            success=success,
            url=storage.get_presigned_url(object_name)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{bucket_name}/{file_name}", status_code=status.HTTP_200_OK, response_model=MainResponse)
async def delete_file(bucket_name: str, file_name: str):
    storage = StorageManage(bucket_name=bucket_name).storage
    try:
        success = storage.delete_file(object_name=file_name)
        return MainResponse(accepted=success)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
