import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional, Tuple
import mimetypes
from dotenv import load_dotenv

# Load environment variables from .env.local and .env files
load_dotenv('.env.local')
load_dotenv('.env')

class S3Service:
    def __init__(self):
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        self.bucket_name = os.getenv('AWS_S3_BUCKET', 'whatsapp-stuff')
        
        # Initialize S3 client
        try:
            self.s3_client = boto3.client(
                's3',
                region_name=self.region,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                aws_session_token=os.getenv('AWS_SESSION_TOKEN')
            )
        except NoCredentialsError:
            raise Exception("AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables.")
    
    def extract_bucket_and_key_from_url(self, s3_url: str) -> Tuple[str, str]:
        """
        Extract bucket and key from S3 URL.
        Example: https://whatsapp-stuff.s3.us-west-2.amazonaws.com/abc/19714594907-s-whatsapp-net/image.jpg
        Returns: (bucket, key)
        """
        try:
            # Remove the scheme (https://)
            if '://' not in s3_url:
                raise ValueError("Invalid S3 URL format")
            
            url_path = s3_url.split('://', 1)[1]
            
            # Split by the first slash to get the domain part
            if '/' not in url_path:
                raise ValueError("Invalid S3 URL format")
            
            domain, key = url_path.split('/', 1)
            
            # Extract bucket name from domain (e.g., "whatsapp-stuff.s3.us-west-2.amazonaws.com" -> "whatsapp-stuff")
            bucket = domain.split('.')[0]
            
            return bucket, key
        except Exception as e:
            raise ValueError(f"Failed to parse S3 URL: {str(e)}")
    
    def get_content_type_from_extension(self, filename: str) -> str:
        """
        Determine content type based on file extension.
        """
        ext = os.path.splitext(filename)[1].lower()
        
        # Comprehensive content type mapping
        content_types = {
            # Images
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp',
            '.svg': 'image/svg+xml',
            '.ico': 'image/x-icon',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff',
            
            # Documents
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.txt': 'text/plain',
            '.rtf': 'application/rtf',
            '.csv': 'text/csv',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.html': 'text/html',
            '.htm': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            
            # Archives
            '.zip': 'application/zip',
            '.rar': 'application/vnd.rar',
            '.7z': 'application/x-7z-compressed',
            '.tar': 'application/x-tar',
            '.gz': 'application/gzip',
            
            # Videos
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.wmv': 'video/x-ms-wmv',
            '.flv': 'video/x-flv',
            '.webm': 'video/webm',
            '.mkv': 'video/x-matroska',
            '.3gp': 'video/3gpp',
            '.m4v': 'video/x-m4v',
            
            # Audio
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.ogg': 'audio/ogg',
            '.aac': 'audio/aac',
            '.flac': 'audio/flac',
            '.m4a': 'audio/mp4',
            '.wma': 'audio/x-ms-wma',
            
            # Code/Text files
            '.py': 'text/x-python',
            '.java': 'text/x-java-source',
            '.cpp': 'text/x-c++src',
            '.cc': 'text/x-c++src',
            '.c': 'text/x-csrc',
            '.php': 'text/x-php',
            '.rb': 'text/x-ruby',
            '.go': 'text/x-go',
            '.rs': 'text/x-rust',
            '.swift': 'text/x-swift',
            '.kt': 'text/x-kotlin',
            '.scala': 'text/x-scala',
            '.sh': 'application/x-sh',
            '.bat': 'application/x-msdos-program',
            '.ps1': 'application/x-powershell',
            
            # Data files
            '.sql': 'application/sql',
            '.yaml': 'application/x-yaml',
            '.yml': 'application/x-yaml',
            '.toml': 'application/toml',
            '.ini': 'text/plain',
            '.conf': 'text/plain',
            '.log': 'text/plain',
        }
        
        return content_types.get(ext, 'application/octet-stream')
    
    def get_file_from_s3(self, s3_url: str) -> Tuple[bytes, str, int]:
        """
        Get file content from S3.
        Returns: (file_content, content_type, content_length)
        """
        try:
            # Extract bucket and key from URL
            bucket, key = self.extract_bucket_and_key_from_url(s3_url)
            
            # Get object from S3
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            
            # Read file content
            file_content = response['Body'].read()
            
            # Determine content type
            content_type = response.get('ContentType')
            if not content_type:
                content_type = self.get_content_type_from_extension(key)
            
            content_length = len(file_content)
            
            return file_content, content_type, content_length
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                raise Exception(f"File not found: {key}")
            elif error_code == 'NoSuchBucket':
                raise Exception(f"Bucket not found: {bucket}")
            else:
                raise Exception(f"S3 error: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to get file from S3: {str(e)}")

# Global S3 service instance
s3_service = S3Service() 