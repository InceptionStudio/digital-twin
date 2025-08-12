import os
import boto3
import logging
from typing import Optional, BinaryIO, Dict, Any
from botocore.exceptions import ClientError, NoCredentialsError
from pathlib import Path
import tempfile
import shutil

logger = logging.getLogger(__name__)

class S3Storage:
    """S3-based file storage for Digital Twin application."""
    
    def __init__(self, bucket_name: str = None):
        from config import Config
        self.bucket_name = bucket_name or Config.S3_BUCKET_NAME
        self.s3_client = None
        self._initialize_s3_client()
    
    def _initialize_s3_client(self):
        """Initialize S3 client with credentials from environment."""
        try:
            # Try to get credentials from environment variables
            aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
            aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            from config import Config
            aws_region = os.getenv('AWS_REGION', Config.AWS_REGION)
            
            if aws_access_key_id and aws_secret_access_key:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    region_name=aws_region
                )
                logger.info(f"S3 client initialized with explicit credentials for region {aws_region}")
            else:
                # Try to use default credentials (IAM roles, etc.)
                self.s3_client = boto3.client('s3', region_name=aws_region)
                logger.info(f"S3 client initialized with default credentials for region {aws_region}")
            
            # Test the connection
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Successfully connected to S3 bucket: {self.bucket_name}")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
            raise
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"S3 bucket '{self.bucket_name}' not found")
                raise
            elif error_code == '403':
                logger.error(f"Access denied to S3 bucket '{self.bucket_name}'")
                raise
            else:
                logger.error(f"S3 client error: {e}")
                raise
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise
    
    def upload_file(self, file_path: str, s3_key: str, content_type: Optional[str] = None) -> str:
        """
        Upload a file to S3 with proper MIME type.
        
        Args:
            file_path: Local path to the file
            s3_key: S3 object key (path in bucket)
            content_type: Optional content type for the file
            
        Returns:
            Permanent S3 URL of the uploaded file
        """
        try:
            extra_args = {}
            
            # Set content type based on file extension if not provided
            if content_type:
                extra_args['ContentType'] = content_type
            else:
                # Auto-detect content type from file extension
                content_type = self._get_content_type_from_filename(s3_key)
                if content_type:
                    extra_args['ContentType'] = content_type
            
            # Try to upload with ACL first, fall back without if not supported
            try:
                extra_args['ACL'] = 'public-read'  # Make file publicly readable
                self.s3_client.upload_file(
                    file_path, 
                    self.bucket_name, 
                    s3_key,
                    ExtraArgs=extra_args
                )
                logger.info(f"File uploaded to S3 with public ACL and content type '{extra_args.get('ContentType', 'unknown')}'")
            except Exception as e:
                # Check if it's an ACL not supported error by checking the error message
                error_str = str(e)
                if 'AccessControlListNotSupported' in error_str:
                    # Remove ACL and try again
                    extra_args.pop('ACL', None)
                    self.s3_client.upload_file(
                        file_path, 
                        self.bucket_name, 
                        s3_key,
                        ExtraArgs=extra_args
                    )
                    logger.info(f"File uploaded to S3 without ACL (bucket doesn't support ACLs) and content type '{extra_args.get('ContentType', 'unknown')}'")
                else:
                    raise
            
            s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
            logger.info(f"File uploaded to S3: {s3_url}")
            return s3_url
            
        except Exception as e:
            logger.error(f"Failed to upload file {file_path} to S3: {e}")
            raise
    
    def _get_content_type_from_filename(self, filename: str) -> Optional[str]:
        """
        Get the appropriate MIME type based on file extension.
        
        Args:
            filename: The filename or S3 key
            
        Returns:
            MIME type string or None if not recognized
        """
        import mimetypes
        
        # Common MIME types for our file types
        mime_types = {
            '.mp3': 'audio/mpeg',
            '.mp4': 'video/mp4',
            '.wav': 'audio/wav',
            '.m4a': 'audio/mp4',
            '.aac': 'audio/aac',
            '.ogg': 'audio/ogg',
            '.webm': 'video/webm',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.mkv': 'video/x-matroska',
            '.flv': 'video/x-flv',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.svg': 'image/svg+xml',
            '.pdf': 'application/pdf',
            '.txt': 'text/plain',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript'
        }
        
        # Get file extension
        file_ext = os.path.splitext(filename.lower())[1]
        
        # Return known MIME type or use Python's mimetypes module as fallback
        if file_ext in mime_types:
            return mime_types[file_ext]
        else:
            # Use Python's built-in mimetypes module as fallback
            guessed_type, _ = mimetypes.guess_type(filename)
            return guessed_type
    
    def upload_fileobj(self, file_obj: BinaryIO, s3_key: str, content_type: Optional[str] = None) -> str:
        """
        Upload a file object to S3 with proper MIME type.
        
        Args:
            file_obj: File-like object to upload
            s3_key: S3 object key (path in bucket)
            content_type: Optional content type for the file
            
        Returns:
            S3 URL of the uploaded file
        """
        try:
            extra_args = {}
            
            # Set content type based on file extension if not provided
            if content_type:
                extra_args['ContentType'] = content_type
            else:
                # Auto-detect content type from file extension
                content_type = self._get_content_type_from_filename(s3_key)
                if content_type:
                    extra_args['ContentType'] = content_type
            
            # Try to upload with ACL first, fall back without if not supported
            try:
                extra_args['ACL'] = 'public-read'  # Make file publicly readable
                self.s3_client.upload_fileobj(
                    file_obj,
                    self.bucket_name,
                    s3_key,
                    ExtraArgs=extra_args
                )
                logger.info(f"File object uploaded to S3 with public ACL and content type '{extra_args.get('ContentType', 'unknown')}'")
            except Exception as e:
                # Check if it's an ACL not supported error by checking the error message
                error_str = str(e)
                if 'AccessControlListNotSupported' in error_str:
                    # Remove ACL and try again
                    extra_args.pop('ACL', None)
                    self.s3_client.upload_fileobj(
                        file_obj,
                        self.bucket_name,
                        s3_key,
                        ExtraArgs=extra_args
                    )
                    logger.info(f"File object uploaded to S3 without ACL (bucket doesn't support ACLs) and content type '{extra_args.get('ContentType', 'unknown')}'")
                else:
                    raise
            
            s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
            logger.info(f"File object uploaded to S3: {s3_url}")
            return s3_url
            
        except Exception as e:
            logger.error(f"Failed to upload file object to S3: {e}")
            raise
    
    def download_file(self, s3_key: str, local_path: str) -> str:
        """
        Download a file from S3 to local storage.
        
        Args:
            s3_key: S3 object key (path in bucket)
            local_path: Local path where to save the file
            
        Returns:
            Local path of the downloaded file
        """
        try:
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)
            logger.info(f"File downloaded from S3: {s3_key} -> {local_path}")
            return local_path
            
        except Exception as e:
            logger.error(f"Failed to download file {s3_key} from S3: {e}")
            raise
    
    def get_file_url(self, s3_key: str, expires_in: int = 3600) -> str:
        """
        Get a presigned URL for a file in S3.
        
        Args:
            s3_key: S3 object key (path in bucket)
            expires_in: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL for the file
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expires_in
            )
            logger.info(f"Generated presigned URL for {s3_key}")
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for {s3_key}: {e}")
            raise
    
    def file_exists(self, s3_key: str) -> bool:
        """
        Check if a file exists in S3.
        
        Args:
            s3_key: S3 object key (path in bucket)
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                logger.error(f"Error checking if file exists {s3_key}: {e}")
                raise
        except Exception as e:
            logger.error(f"Failed to check if file exists {s3_key}: {e}")
            raise
    
    def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3.
        
        Args:
            s3_key: S3 object key (path in bucket)
            
        Returns:
            True if file was deleted, False if file didn't exist
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"File deleted from S3: {s3_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file {s3_key} from S3: {e}")
            raise
    
    def list_files(self, prefix: str = "", max_keys: int = 1000) -> list:
        """
        List files in S3 bucket with optional prefix.
        
        Args:
            prefix: Optional prefix to filter files
            max_keys: Maximum number of keys to return
            
        Returns:
            List of file keys
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            files = []
            if 'Contents' in response:
                files = [obj['Key'] for obj in response['Contents']]
            
            logger.info(f"Listed {len(files)} files from S3 with prefix '{prefix}'")
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files from S3: {e}")
            raise
    
    def get_file_info(self, s3_key: str) -> Dict[str, Any]:
        """
        Get information about a file in S3.
        
        Args:
            s3_key: S3 object key (path in bucket)
            
        Returns:
            Dictionary with file information
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            
            info = {
                'key': s3_key,
                'size': response['ContentLength'],
                'content_type': response.get('ContentType', ''),
                'last_modified': response['LastModified'],
                'etag': response['ETag'].strip('"')
            }
            
            logger.info(f"Retrieved file info for {s3_key}")
            return info
            
        except Exception as e:
            logger.error(f"Failed to get file info for {s3_key}: {e}")
            raise
    
    def copy_file(self, source_key: str, dest_key: str) -> str:
        """
        Copy a file within the same S3 bucket.
        
        Args:
            source_key: Source S3 object key
            dest_key: Destination S3 object key
            
        Returns:
            S3 URL of the copied file
        """
        try:
            copy_source = {'Bucket': self.bucket_name, 'Key': source_key}
            self.s3_client.copy(copy_source, self.bucket_name, dest_key)
            
            s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{dest_key}"
            logger.info(f"File copied in S3: {source_key} -> {dest_key}")
            return s3_url
            
        except Exception as e:
            logger.error(f"Failed to copy file {source_key} to {dest_key}: {e}")
            raise
