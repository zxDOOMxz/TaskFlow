import io
from typing import Optional
from uuid import uuid4

from minio import Minio

from app.config import get_settings

settings = get_settings()


def get_minio_client() -> Minio:
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=False,
    )


def ensure_bucket():
    client = get_minio_client()
    if not client.bucket_exists(settings.minio_bucket):
        client.make_bucket(settings.minio_bucket)


def upload_file(
    file_data: bytes,
    filename: str,
    content_type: str,
    entity_type: Optional[str] = None,
) -> str:
    ensure_bucket()
    client = get_minio_client()

    ext = filename.split(".")[-1] if "." in filename else ""
    storage_key = f"{entity_type or 'files'}/{uuid4()}.{ext}" if ext else f"{entity_type or 'files'}/{uuid4()}"

    client.put_object(
        bucket_name=settings.minio_bucket,
        object_name=storage_key,
        data=io.BytesIO(file_data),
        length=len(file_data),
        content_type=content_type,
    )
    return storage_key


def get_presigned_url(storage_key: str, expires: int = 3600) -> str:
    client = get_minio_client()
    return client.presigned_get_object(settings.minio_bucket, storage_key, expires=expires)


def delete_file(storage_key: str):
    client = get_minio_client()
    client.remove_object(settings.minio_bucket, storage_key)
