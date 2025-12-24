from abc import ABC, abstractmethod
from typing import Optional, BinaryIO


class StorageAction(ABC):

    @abstractmethod
    def create_bucket(self, bucket_name: str, acl: str = 'private') -> bool:
        """
        Create a new bucket in S3 storage.

        Args:
            bucket_name: Name of the bucket to create
            acl: Access control list (private, public-read, public-read-write, etc.)

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def download_file(self, object_name: str, bucket_name: str, file_path: str) -> bool:
        """
        Download a file from S3 storage.

        Args:
            object_name: S3 object name
            file_path: Local path to save the file

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def delete_file(self, object_name: str, bucket_name: str) -> bool:
        """
        Delete a file from S3 storage.

        Args:
            object_name: S3 object name to delete

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def list_files(self, bucket_name: str, prefix: str = "") -> list:
        """
        List files in S3 storage.

        Args:
            bucket_name: Bucket name or did where the file will be stored
            prefix: Optional prefix to filter files

        Returns:
            List of object keys
        """
        pass

    @abstractmethod
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
        pass
