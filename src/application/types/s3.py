import os
import logging
import boto3
from typing import Optional, BinaryIO
from botocore.exceptions import ClientError

from config.settings import settings
from src.application.types.storage import StorageAction

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


class S3StorageActions(StorageAction):
    """Service for storing files in S3-compatible storage."""

    def __init__(
            self,
            endpoint_url: Optional[str] = None,
            access_key: Optional[str] = None,
            secret_key: Optional[str] = None,
            region: str = "us-east-1"
    ):
        """
        Initialize S3 storage service.

        Args:
            endpoint_url: S3-compatible endpoint (e.g., MinIO, DigitalOcean Spaces)
            access_key: Access key ID
            secret_key: Secret access key
            bucket_name: Name of the bucket to use
            region: AWS region
        """

        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key or os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=secret_key or os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=region
        )

    def create_bucket(self, bucket_name: str, acl: str = 'private') -> bool:
        """
        Create a new bucket in S3 storage.

        Args:
            bucket_name: Name of the bucket to create
            acl: Access control list (private, public-read, public-read-write, etc.)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if bucket already exists
            try:
                self.s3_client.head_bucket(Bucket=bucket_name)
                logger.warning(f"Bucket '{bucket_name}' already exists")
                return True
            except ClientError as e:
                if e.response['Error']['Code'] != '404':
                    raise

            # Create the bucket
            self.s3_client.create_bucket(
                Bucket=bucket_name,
                ACL=acl
            )
            logger.info(f"Successfully created bucket '{bucket_name}' with ACL '{acl}'")
            return True
        except ClientError as e:
            logger.error(f"Failed to create bucket '{bucket_name}': {e}")
            return False

    def upload_fileobj(
            self,
            file_obj: BinaryIO,
            object_name: str,
            bucket_name: str,
            metadata: Optional[dict] = None
    ) -> bool:
        """
        Upload a file-like object to S3 storage.

        Args:
            file_obj: File-like object to upload
            object_name: S3 object name
            bucket_name: Bucket name or did where the file will be stored
            metadata: Optional metadata dictionary

        Returns:
            True if successful, False otherwise
        """
        extra_args = {}
        if metadata:
            extra_args['Metadata'] = metadata

        try:
            self.s3_client.upload_fileobj(
                file_obj,
                bucket_name,
                object_name,
                ExtraArgs=extra_args if extra_args else None
            )
            logger.info(f"Successfully uploaded file object as '{object_name}'")
            return True
        except ClientError as e:
            logger.error(f"Failed to upload file object: {e}")
            return False

    def download_file(self, object_name: str, bucket_name: str, file_path: str) -> bool:
        """
        Download a file from S3 storage.

        Args:
            object_name: S3 object name
            bucket_name: Bucket name or did where the file will be stored
            file_path: Local path to save the file
        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.download_file(bucket_name, object_name, file_path)
            logger.info(f"Successfully downloaded '{object_name}' to '{file_path}'")
            return True
        except ClientError as e:
            logger.error(f"Failed to download file: {e}")
            return False

    def delete_file(self, object_name: str, bucket_name: str) -> bool:
        """
        Delete a file from S3 storage.

        Args:
            object_name: S3 object name to delete
            bucket_name: Bucket name or did where the file will be stored

        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=object_name)
            logger.info(f"Successfully deleted '{object_name}'")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file: {e}")
            return False

    def list_files(self, bucket_name: str, prefix: str = "", ) -> list:
        """
        List files in S3 storage.

        Args:
            bucket_name: Bucket name or did where the file will be stored
            prefix: Optional prefix to filter files

        Returns:
            List of object keys
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix
            )

            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            return []
        except ClientError as e:
            logger.error(f"Failed to list files: {e}")
            return []

    def get_presigned_url(
            self,
            bucket_name: str,
            object_name: str,
            expiration: int = 3600
    ) -> Optional[str]:
        """
        Generate a presigned URL for downloading a file.

        Args:
            bucket_name: Bucket name or did where the file will be stored
            object_name: S3 object name
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            Presigned URL or None if failed
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_name},
                ExpiresIn=expiration
            )
            logger.info(f"Generated presigned URL for '{object_name}'")
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None
