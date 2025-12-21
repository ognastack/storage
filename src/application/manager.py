from config.settings import settings

from src.application.types.storage import StorageAction
from src.application.types.s3 import S3StorageActions
from src.application.types.local import LocalStorageActions


class StorageManage:

    def __init__(self, bucket_name):
        self.storage: StorageAction = S3StorageActions(
            endpoint_url=settings.S3_ENDPOINT_URL,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            bucket_name=bucket_name
        ) if settings.STORAGE_TYPE == "S3" else LocalStorageActions()
