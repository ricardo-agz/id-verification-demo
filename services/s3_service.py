import traceback
from typing import Optional
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import os
from datetime import datetime


class S3Service:
    def __init__(self, bucket_name: str, aws_region: str = "us-east-1"):
        self.bucket_name = bucket_name
        self.aws_region = aws_region
        self.s3_client = boto3.client("s3", region_name=aws_region)

    def _check_bucket_exists(self) -> bool:
        """Check if the configured bucket exists and is accessible."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError:
            return False

    def _ensure_bucket_exists(self) -> None:
        """Ensure the configured bucket exists, creating it if necessary."""
        if not self._check_bucket_exists():
            try:
                if self.aws_region == "us-east-1":
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                else:
                    location = {"LocationConstraint": self.aws_region}
                    self.s3_client.create_bucket(
                        Bucket=self.bucket_name,
                        CreateBucketConfiguration=location
                    )
            except ClientError as e:
                raise Exception(f"Failed to create bucket: {str(e)}")

    def upload_document(self, file_path: str, document_type: str) -> Optional[str]:
        if not file_path or not isinstance(file_path, str):
            raise ValueError("Invalid file path")

        if not document_type or not isinstance(document_type, str):
            raise ValueError("Invalid document type")

        if not os.path.exists(file_path):
            raise ValueError(f"File does not exist: {file_path}")

        if os.path.getsize(file_path) == 0:
            raise ValueError(f"File is empty: {file_path}")

        try:
            self._ensure_bucket_exists()

            timestamp = datetime.utcnow().strftime('%Y/%m/%d/%H%M%S')
            file_extension = os.path.splitext(file_path)[1]
            if not file_extension:
                file_extension = '.jpg'  # Default extension if none is found

            safe_document_type = document_type.lower().replace(' ', '_')
            s3_key = f"documents/{safe_document_type}/{timestamp}{file_extension}"

            self.s3_client.upload_file(
                Filename=file_path,
                Bucket=self.bucket_name,
                Key=s3_key
            )

            return self.get_public_url(s3_key)

        except NoCredentialsError:
            raise Exception("AWS credentials not available")
        except ClientError as e:
            raise Exception(f"Failed to upload document: {str(e)}")
        except Exception as e:
            print(traceback.format_exc())
            raise Exception(f"Error uploading document: {str(e)}")

    def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> str:
        """
        Generate a pre-signed URL for temporary access to an S3 object.

        Args:
            s3_key: The S3 key of the object
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            str: Pre-signed URL for the object
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            raise Exception(f"Error generating pre-signed URL: {str(e)}")

    def get_public_url(self, s3_key: str) -> str:
        """
        Generate a public HTTPS URL for an S3 object.
        Note: Bucket must be configured for public access for this URL to work.

        Args:
            s3_key: The S3 key of the object

        Returns:
            str: Public URL for the object
        """
        return f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{s3_key}"
