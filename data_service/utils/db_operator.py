import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from minio import Minio
from minio.error import S3Error
from io import BytesIO
import urllib3

# Disable SSL warnings for local development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class S3Operator:
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        secure: bool = False,
        region: str = "us-east-1"
    ):
        """
        Initialize MinIO S3 client

        Args:
            endpoint: MinIO server endpoint (e.g., 'localhost:9000')
            access_key: MinIO access key
            secret_key: MinIO secret key
            bucket_name: Default bucket name
            secure: Use HTTPS (False for local development)
            region: AWS region (for compatibility)
        """
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            region=region
        )
        self.bucket_name = bucket_name
        self.logger = logging.getLogger(__name__)

        # Ensure bucket exists
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                self.logger.info(f"Created bucket: {self.bucket_name}")
            else:
                self.logger.info(f"Bucket {self.bucket_name} already exists")
        except S3Error as e:
            self.logger.error(f"Failed to create/check bucket {self.bucket_name}: {e}")
            raise

    def upload_json(self, key: str, data: Dict, metadata: Optional[Dict] = None) -> bool:
        """
        Upload JSON data to MinIO

        Args:
            key: Object key/path in bucket
            data: Dictionary to upload as JSON
            metadata: Optional metadata tags

        Returns:
            bool: Success status
        """
        try:
            json_data = json.dumps(data, ensure_ascii=False)
            json_bytes = json_data.encode('utf-8')

            # Create BytesIO object
            data_stream = BytesIO(json_bytes)

            # Upload to MinIO
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=key,
                data=data_stream,
                length=len(json_bytes),
                content_type='application/json',
                metadata=metadata or {}
            )

            self.logger.info(f"Successfully uploaded {key} to {self.bucket_name}")
            return True

        except S3Error as e:
            self.logger.error(f"Failed to upload {key}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error uploading {key}: {e}")
            return False

    def download_json(self, key: str) -> Optional[Dict]:
        """
        Download JSON data from MinIO

        Args:
            key: Object key/path in bucket

        Returns:
            Dict: Downloaded JSON data or None if failed
        """
        try:
            response = self.client.get_object(self.bucket_name, key)
            json_data = response.read().decode('utf-8')

            self.logger.info(f"Successfully downloaded {key} from {self.bucket_name}")
            return json.loads(json_data)

        except S3Error as e:
            self.logger.error(f"Failed to download {key}: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON from {key}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error downloading {key}: {e}")
            return None
        finally:
            if 'response' in locals():
                response.close()
                response.release_conn()

    def upload_file(self, key: str, file_path: str, content_type: str = None) -> bool:
        """
        Upload file to MinIO

        Args:
            key: Object key/path in bucket
            file_path: Local file path
            content_type: MIME type (auto-detected if None)

        Returns:
            bool: Success status
        """
        try:
            self.client.fput_object(
                bucket_name=self.bucket_name,
                object_name=key,
                file_path=file_path,
                content_type=content_type
            )

            self.logger.info(f"Successfully uploaded file {file_path} as {key}")
            return True

        except S3Error as e:
            self.logger.error(f"Failed to upload file {file_path}: {e}")
            return False

    def download_file(self, key: str, file_path: str) -> bool:
        """
        Download file from MinIO

        Args:
            key: Object key/path in bucket
            file_path: Local file path to save

        Returns:
            bool: Success status
        """
        try:
            self.client.fget_object(
                bucket_name=self.bucket_name,
                object_name=key,
                file_path=file_path
            )

            self.logger.info(f"Successfully downloaded {key} to {file_path}")
            return True

        except S3Error as e:
            self.logger.error(f"Failed to download {key}: {e}")
            return False

    def list_objects(self, prefix: str = "", recursive: bool = False) -> List[str]:
        """
        List objects in bucket

        Args:
            prefix: Object prefix filter
            recursive: List recursively

        Returns:
            List[str]: List of object keys
        """
        try:
            objects = self.client.list_objects(
                bucket_name=self.bucket_name,
                prefix=prefix,
                recursive=recursive
            )

            object_keys = [obj.object_name for obj in objects]
            self.logger.info(f"Found {len(object_keys)} objects with prefix '{prefix}'")
            return object_keys

        except S3Error as e:
            self.logger.error(f"Failed to list objects: {e}")
            return []

    def delete_object(self, key: str) -> bool:
        """
        Delete object from MinIO

        Args:
            key: Object key/path to delete

        Returns:
            bool: Success status
        """
        try:
            self.client.remove_object(self.bucket_name, key)
            self.logger.info(f"Successfully deleted {key}")
            return True

        except S3Error as e:
            self.logger.error(f"Failed to delete {key}: {e}")
            return False

    def object_exists(self, key: str) -> bool:
        """
        Check if object exists in bucket

        Args:
            key: Object key/path to check

        Returns:
            bool: True if object exists
        """
        try:
            self.client.stat_object(self.bucket_name, key)
            return True
        except S3Error:
            return False

    def get_object_metadata(self, key: str) -> Optional[Dict]:
        """
        Get object metadata

        Args:
            key: Object key/path

        Returns:
            Dict: Object metadata or None if failed
        """
        try:
            stat = self.client.stat_object(self.bucket_name, key)
            return {
                'size': stat.size,
                'last_modified': stat.last_modified,
                'etag': stat.etag,
                'content_type': stat.content_type,
                'metadata': stat.metadata
            }
        except S3Error as e:
            self.logger.error(f"Failed to get metadata for {key}: {e}")
            return None

    def create_presigned_url(self, key: str, expires_in_seconds: int = 3600) -> Optional[str]:
        """
        Create presigned URL for object access

        Args:
            key: Object key/path
            expires_in_seconds: URL expiration time

        Returns:
            str: Presigned URL or None if failed
        """
        try:
            from datetime import timedelta
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=key,
                expires=timedelta(seconds=expires_in_seconds)
            )
            return url
        except S3Error as e:
            self.logger.error(f"Failed to create presigned URL for {key}: {e}")
            return None
