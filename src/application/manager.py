import uuid
import logging
from fastapi import UploadFile

from config.settings import settings
from src.application.types.storage import StorageAction
from src.application.types.s3 import S3StorageActions
from src.application.types.local import LocalStorageActions

from src.schema.response.storage import NewBucket
from src.schema.requests.storage import Bucket
from src.database.database import DatabaseEngine
from src.core.exceptions import BucketNotFound

from src.schema.requests.storage import FileObject

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


class StorageManager:

    def __init__(self, bucket_name, user_token):
        self.bucket_name = bucket_name
        self.storage: StorageAction = S3StorageActions(
            endpoint_url=settings.S3_ENDPOINT_URL,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY
        ) if settings.STORAGE_TYPE == "S3" else LocalStorageActions()
        self.engine = DatabaseEngine(token=user_token)

    def create_bucket(self, bucket_data: Bucket, current_user: uuid.UUID) -> NewBucket:
        logger.info(f"Creating bucket {bucket_data.name}")
        bucket = self.engine.create_bucket(
            bucket_data=bucket_data,
            user_id=current_user
        )
        complete = self.storage.create_bucket(bucket_name=str(bucket.id))
        return NewBucket(accepted=complete)

    def upload_file(self, file: UploadFile, current_user: uuid.UUID) -> str:
        logger.info(f"Uploading bucket {file.filename}")

        bucket = self.engine.get_bucket_by_id_user(
            bucket_name=self.bucket_name,
            owner_id=current_user
        )

        if bucket is None:
            raise BucketNotFound(self.bucket_name)

        self.engine.create_file(
            bucket_name=bucket.name,
            file_name=file.filename,
            owner_id=current_user
        )

        object_name = file.filename

        self.storage.upload_fileobj(
            file_obj=file.file,
            bucket_name=str(bucket.id),
            object_name=object_name
        )

        return self.storage.get_presigned_url(
            object_name=object_name,
            bucket_name=str(bucket.id)
        )

    def delete_file(self, file_name: str, current_user: uuid.UUID) -> bool:
        logger.info(f"Deleting bucket {file_name}")
        search_file = self.engine.get_file(
            bucket_name=self.bucket_name,
            file_name=file_name,
            owner_id=current_user
        )

        if search_file is None:
            raise FileNotFoundError(2, "No such file or directory", file_name)

        self.engine.delete_file(
            bucket_name=self.bucket_name,
            owner_id=current_user,
            file_name=file_name
        )

        return self.storage.delete_file(object_name=file_name, bucket_name=str(search_file.bucket_id))

    def get_file(self, file_name: str, current_user: uuid.UUID):
        logger.info(f"Getting bucket {file_name}")

        store_file = self.engine.get_file(
            bucket_name=self.bucket_name,
            file_name=file_name,
            owner_id=current_user
        )

        if store_file is None:
            raise FileNotFoundError(2, "No such file or directory", file_name)

        logger.info(store_file)

        file_path = f"/tmp/{str(current_user)}"

        self.storage.download_file(
            object_name=file_name,
            file_path=file_path,
            bucket_name=str(store_file.bucket_id)
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
