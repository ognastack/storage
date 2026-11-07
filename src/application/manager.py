import uuid
import logging
import os
import re
import tempfile
from typing import Optional
from fastapi import UploadFile, HTTPException, status

from config.settings import settings
from src.application.types.storage import StorageAction
from src.application.types.s3 import S3StorageActions
from src.application.types.local import LocalStorageActions

from src.schema.response.storage import NewBucket
from src.schema.requests.storage import Bucket
from src.database.database import DatabaseEngine
from src.core.exceptions import BucketNotFound, ValidationError

from src.schema.requests.storage import FileObject

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

SAFE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._ -]{0,253}[a-zA-Z0-9]$|^[a-zA-Z0-9]$")


def validate_safe_name(value: Optional[str], field_label: str = "file_name") -> str:
    """Validate bucket or file names against path traversal and unsafe characters."""
    if not value or not value.strip():
        raise ValidationError(f"Invalid {field_label}: cannot be empty")
    cleaned = value.strip()
    if (
        ".." in cleaned
        or "/" in cleaned
        or "\\" in cleaned
        or "\x00" in cleaned
        or os.path.basename(cleaned) != cleaned
        or not SAFE_NAME_PATTERN.match(cleaned)
    ):
        raise ValidationError(
            f"Invalid {field_label}: must not contain path separators, '..', or special control characters"
        )
    return cleaned


class StorageManager:

    def __init__(self, bucket_name, user_token):
        self.bucket_name = validate_safe_name(bucket_name, "bucket_name") if bucket_name else ""
        self.storage: StorageAction = S3StorageActions(
            endpoint_url=settings.S3_ENDPOINT_URL,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            region=settings.S3_REGION or settings.AWS_REGION or settings.AWS_DEFAULT_REGION
        ) if settings.STORAGE_TYPE == "S3" else LocalStorageActions()
        self.engine = DatabaseEngine(token=user_token)

    @staticmethod
    def _validate_upload_size(file: UploadFile) -> None:
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file.size is not None and file.size > max_bytes:
            raise ValidationError(
                f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB} MB"
            )
        file.file.seek(0, os.SEEK_END)
        actual_size = file.file.tell()
        file.file.seek(0)
        if actual_size > max_bytes:
            raise ValidationError(
                f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB} MB"
            )

    def create_bucket(self, bucket_data: Bucket, current_user: uuid.UUID) -> NewBucket:
        logger.info(f"Creating bucket {bucket_data.name}")
        bucket = self.engine.create_bucket(
            bucket_data=bucket_data,
            user_id=current_user
        )
        complete = self.storage.create_bucket(bucket_name=str(bucket.id))
        return NewBucket(accepted=complete)

    def get_bucket(self, current_user: uuid.UUID) -> Bucket:
        logger.info(f"Getting bucket {self.bucket_name}")
        bucket = self.engine.get_bucket_by_id_user(
            bucket_name=self.bucket_name,
            owner_id=current_user
        )
        if bucket is None:
            raise BucketNotFound(self.bucket_name)
        return bucket

    def delete_bucket(self, current_user: uuid.UUID) -> bool:
        logger.info(f"Deleting bucket {self.bucket_name}")
        bucket = self.engine.get_bucket_by_id_user(
            bucket_name=self.bucket_name,
            owner_id=current_user
        )
        if bucket is None:
            raise BucketNotFound(self.bucket_name)

        storage_deleted = self.storage.delete_bucket(bucket_name=str(bucket.id))
        db_deleted = self.engine.delete_bucket(bucket_name=self.bucket_name, owner_id=current_user)
        return storage_deleted and db_deleted

    def upload_file(
            self,
            file: UploadFile,
            current_user: uuid.UUID,
            file_name: Optional[str] = None
    ) -> tuple[str, str]:
        object_name = validate_safe_name(file_name or file.filename, "file_name")
        self._validate_upload_size(file)
        logger.info(f"Uploading file {object_name} to bucket {self.bucket_name}")

        bucket = self.engine.get_bucket_by_id_user(
            bucket_name=self.bucket_name,
            owner_id=current_user
        )

        if bucket is None:
            raise BucketNotFound(self.bucket_name)

        create_file_response = self.engine.create_file(
            bucket_name=bucket.name,
            file_name=object_name,
            owner_id=current_user
        )

        self.storage.upload_fileobj(
            file_obj=file.file,
            bucket_name=str(bucket.id),
            object_name=object_name
        )

        return self.storage.get_presigned_url(
            object_name=object_name,
            bucket_name=str(bucket.id)
        ), str(create_file_response['id'])

    def delete_file(self, file_name: str, current_user: uuid.UUID) -> bool:
        safe_file_name = validate_safe_name(file_name, "file_name")
        logger.info(f"Deleting file {safe_file_name} from bucket {self.bucket_name}")
        search_file = self.engine.get_file(
            bucket_name=self.bucket_name,
            file_name=safe_file_name,
            owner_id=current_user
        )

        if search_file is None:
            raise FileNotFoundError(2, "No such file or directory", safe_file_name)

        self.engine.delete_file(
            bucket_name=self.bucket_name,
            owner_id=current_user,
            file_name=safe_file_name
        )

        return self.storage.delete_file(object_name=safe_file_name, bucket_name=str(search_file.bucket_id))

    def get_file(self, file_name: str, current_user: uuid.UUID):
        safe_file_name = validate_safe_name(file_name, "file_name")
        logger.info(f"Getting file {safe_file_name} from bucket {self.bucket_name}")

        store_file = self.engine.get_file(
            bucket_name=self.bucket_name,
            file_name=safe_file_name,
            owner_id=current_user
        )

        if store_file is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File record '{safe_file_name}' not found in database"
            )

        logger.info(store_file)

        # Build a confined path in the system temp directory to prevent path traversal
        tmp_dir = os.path.realpath(tempfile.gettempdir())
        candidate_name = f"{str(current_user)}_{uuid.uuid4().hex[:8]}_{os.path.basename(safe_file_name)}"
        file_path = os.path.realpath(os.path.join(tmp_dir, candidate_name))
        if not file_path.startswith(tmp_dir + os.sep):
            raise ValidationError("Invalid file path")

        success = self.storage.download_file(
            object_name=safe_file_name,
            file_path=file_path,
            bucket_name=str(store_file.bucket_id)
        )

        if not success or not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File content '{safe_file_name}' missing from storage engine"
            )

        return file_path

    def get_files(self, current_user: uuid.UUID) -> list[FileObject]:

        return self.engine.get_files(
            bucket_name=self.bucket_name,
            owner_id=current_user
        )

    def get_buckets(self, current_user: uuid.UUID):
        results = self.engine.get_buckets(
            owner_id=current_user
        )
        return [bucket for bucket in results]
