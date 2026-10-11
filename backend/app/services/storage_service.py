import logging
import boto3
from botocore.exceptions import ClientError
from app.config.settings import get_settings

settings = get_settings()

logger = logging.getLogger("app")

class StorageService:
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=getattr(settings, "S3_ENDPOINT_URL", None),
            aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", "your-key"),
            aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", "your-secret"),
            region_name=getattr(settings, "AWS_REGION", "us-east-1"),
        )
        self.bucket_name = getattr(settings, "S3_BUCKET_NAME", "astrology-platform-assets")

    def upload_file_bytes(self, file_bytes: bytes, destination_path: str, content_type: str = "image/png") -> str:
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=destination_path,
                Body=file_bytes,
                ContentType=content_type,
            )
            cdn_url = getattr(settings, "S3_PUBLIC_DOMAIN", None)
            if cdn_url:
                return f"{cdn_url.rstrip('/')}/{destination_path}"
            return f"https://{self.bucket_name}.s3.amazonaws.com/{destination_path}"
        except ClientError as e:
            logger.exception("S3/R2 Dosya Yükleme Hatası:")
            raise e

storage_service = StorageService()
