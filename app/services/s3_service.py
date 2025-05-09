"""
S3 Service for handling document storage and retrieval.
Manages S3 operations for the application.
"""
import boto3
from botocore.exceptions import ClientError
import logging
from typing import Dict, Optional

from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class S3Service:
    """
    Service for interacting with AWS S3.
    
    Attributes:
        s3_client: Boto3 S3 client
        bucket_name: S3 bucket name
    """
    
    def __init__(self):
        """Initialize S3 service with configurations."""
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_DEFAULT_REGION,
        )
        self.bucket_name = settings.S3_BUCKET_NAME
    
    def upload_file(self, file_content: bytes, key: str, content_type: Optional[str] = None) -> bool:
        """
        Upload a file to S3.
        
        Args:
            file_content: Content of the file
            key: S3 key (path) for the file
            content_type: MIME type of the file
            
        Returns:
            True if upload was successful, False otherwise
        """
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_content,
                **extra_args
            )
            logger.info(f"Successfully uploaded file to {key}")
            return True
        except ClientError as e:
            logger.error(f"Error uploading file to S3: {e}")
            return False
    
    def get_download_url(self, key: str, expiry: int = None) -> Optional[str]:
        """
        Generate a pre-signed URL for downloading a file from S3.
        
        Args:
            key: S3 key (path) of the file
            expiry: Expiry time in seconds (default: from settings)
            
        Returns:
            Pre-signed URL for downloading the file or None if error
        """
        if expiry is None:
            expiry = settings.S3_DOCUMENT_EXPIRY_TIME
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key
                },
                ExpiresIn=expiry
            )
            return url
        except ClientError as e:
            logger.error(f"Error generating pre-signed URL: {e}")
            return None
    
    def delete_file(self, key: str) -> bool:
        """
        Delete a file from S3.
        
        Args:
            key: S3 key (path) of the file to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            logger.info(f"Successfully deleted file {key}")
            return True
        except ClientError as e:
            logger.error(f"Error deleting file from S3: {e}")
            return False
    
    def check_file_exists(self, key: str) -> bool:
        """
        Check if a file exists in S3.
        
        Args:
            key: S3 key (path) of the file to check
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            logger.error(f"Error checking if file exists: {e}")
            return False