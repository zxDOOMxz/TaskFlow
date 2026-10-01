import io
from typing import Optional
from uuid import uuid4

import httpx
from minio import Minio

from app.config import Settings, get_settings

settings = get_settings()


def _supabase_headers(settings: Settings) -> dict:
    return {
        "apikey": settings.supabase_publishable_key or settings.supabase_secret_or_key,
        "Authorization": f"Bearer {settings.supabase_secret_or_key}",
    }


def _ensure_supabase_bucket(settings: Settings):
    url = f"{settings.supabase_url}/storage/v1/bucket"
    bucket_id = "taskflow"
    try:
        response = httpx.post(
            url,
            headers={**_supabase_headers(settings), "Content-Type": "application/json"},
            json={"id": bucket_id, "name": bucket_id, "public": False},
            timeout=10.0,
        )
        if response.status_code not in (200, 201):
            # Bucket may already exist
            pass
    except Exception:
        pass


def upload_file_supabase(
    file_data: bytes,
    filename: str,
    content_type: str,
    entity_type: Optional[str] = None,
    settings: Settings = None,
) -> str:
    settings = settings or get_settings()
    _ensure_supabase_bucket(settings)

    ext = filename.split(".")[-1] if "." in filename else ""
    storage_key = f"{entity_type or 'files'}/{uuid4()}.{ext}" if ext else f"{entity_type or 'files'}/{uuid4()}"

    url = f"{settings.supabase_url}/storage/v1/object/taskflow/{storage_key}"
    response = httpx.post(
        url,
        headers={**_supabase_headers(settings), "Content-Type": content_type, "x-upsert": "false"},
        content=file_data,
        timeout=60.0,
    )
    response.raise_for_status()
    return storage_key


def get_presigned_url_supabase(
    storage_key: str, expires: int = 3600, settings: Settings = None
) -> str:
    settings = settings or get_settings()
    url = f"{settings.supabase_url}/storage/v1/object/sign/taskflow/{storage_key}"
    response = httpx.post(
        url,
        headers={**_supabase_headers(settings), "Content-Type": "application/json"},
        json={"expiresIn": expires},
        timeout=10.0,
    )
    response.raise_for_status()
    data = response.json()
    signed_path = data.get("signedURL")
    if not signed_path:
        raise RuntimeError("Supabase did not return signedURL")
    return f"{settings.supabase_url}{signed_path}"


def delete_file_supabase(storage_key: str, settings: Settings = None):
    settings = settings or get_settings()
    url = f"{settings.supabase_url}/storage/v1/object/taskflow/{storage_key}"
    response = httpx.delete(url, headers=_supabase_headers(settings), timeout=10.0)
    response.raise_for_status()


# MinIO helpers (existing)
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


def upload_file_minio(
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


def get_presigned_url_minio(storage_key: str, expires: int = 3600) -> str:
    client = get_minio_client()
    return client.presigned_get_object(settings.minio_bucket, storage_key, expires=expires)


def delete_file_minio(storage_key: str):
    client = get_minio_client()
    client.remove_object(settings.minio_bucket, storage_key)


# Unified interface
def _use_supabase() -> bool:
    s = get_settings()
    return s.is_supabase_enabled and bool(s.supabase_secret_or_key)


def upload_file(
    file_data: bytes,
    filename: str,
    content_type: str,
    entity_type: Optional[str] = None,
) -> str:
    if _use_supabase():
        return upload_file_supabase(file_data, filename, content_type, entity_type)
    return upload_file_minio(file_data, filename, content_type, entity_type)


def get_presigned_url(storage_key: str, expires: int = 3600) -> str:
    if _use_supabase():
        return get_presigned_url_supabase(storage_key, expires)
    return get_presigned_url_minio(storage_key, expires)


def delete_file(storage_key: str):
    if _use_supabase():
        return delete_file_supabase(storage_key)
    return delete_file_minio(storage_key)
