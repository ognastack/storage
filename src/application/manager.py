import uuid

from config.settings import settings
from fastapi import UploadFile

from src.application.types.storage import StorageAction
from src.application.types.s3 import S3StorageActions
from src.application.types.local import LocalStorageActions

from src.schema.response.storage import NewBucket
from src.schema.requests.storage import Bucket
from src.database.database import DatabaseEngine
from src.core.exceptions import BucketNotFound


class StorageManager:

    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        self.storage: StorageAction = S3StorageActions(
            endpoint_url=settings.S3_ENDPOINT_URL,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            bucket_name=self.bucket_name
        ) if settings.STORAGE_TYPE == "S3" else LocalStorageActions()

    def create_bucket(self, bucket_data: Bucket, current_user: uuid.UUID) -> NewBucket:
        engine = DatabaseEngine()
        bucket = engine.create_bucket(
            bucket_data=bucket_data,
            user_id=current_user
        )
        complete = self.storage.create_bucket(bucket_name=str(bucket.id))
        return NewBucket(accepted=complete)

    def upload_file(self, file: UploadFile, current_user: uuid.UUID) -> str:
        engine = DatabaseEngine()
        bucket = engine.get_bucket_by_id_user(
            bucket_name=self.bucket_name,
            owner_id=current_user
        )

        if bucket is None:
            raise BucketNotFound(self.bucket_name)

        engine.create_file(
            bucket_name=bucket.name,
            file_name=file.filename,
            owner_id=current_user
        )
        self.storage.create_bucket(self.bucket_name)
        object_name = file.filename

        self.storage.upload_fileobj(
            file_obj=file.file,
            object_name=object_name
        )

        return self.storage.get_presigned_url(object_name)

    def delete_file(self, file_name: str, current_user: uuid.UUID):
        engine = DatabaseEngine()

        engine.delete_file(
            bucket_name=self.bucket_name,
            owner_id=current_user,
            file_name=file_name
        )

        return True

