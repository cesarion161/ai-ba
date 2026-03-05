from __future__ import annotations

from typing import Any

import boto3
import structlog

from app.core.config import get_settings

logger = structlog.get_logger()


class S3Storage:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._client = None

    def _get_client(self) -> Any:
        if self._client is None:
            self._client = boto3.client(
                "s3",
                region_name=self.settings.S3_REGION,
                aws_access_key_id=self.settings.AWS_ACCESS_KEY_ID or None,
                aws_secret_access_key=self.settings.AWS_SECRET_ACCESS_KEY or None,
            )
        return self._client

    async def upload(
        self, key: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> str:
        client = self._get_client()
        client.put_object(
            Bucket=self.settings.S3_BUCKET,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        logger.info("s3_upload", key=key, size=len(data))
        return key

    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        client = self._get_client()
        url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.settings.S3_BUCKET, "Key": key},
            ExpiresIn=expires_in,
        )
        return str(url)

    async def download(self, key: str) -> bytes:
        client = self._get_client()
        response = client.get_object(Bucket=self.settings.S3_BUCKET, Key=key)
        return bytes(response["Body"].read())


s3_storage = S3Storage()
