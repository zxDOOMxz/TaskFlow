from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://taskflow:taskflow@db:5432/taskflow"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"
    cors_origins: str = "http://localhost:5173"

    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "taskflow"

    # Web3Forms (https://web3forms.com/) for contact/invite forms without a backend SMTP server
    web3forms_access_key: str = ""
    web3forms_endpoint: str = "https://api.web3forms.com/submit"
    web3forms_enabled: bool = False

    # Supabase integration (Auth + PostgreSQL)
    supabase_url: str = ""
    supabase_key: str = ""  # service_role / secret key for backend admin access
    supabase_secret_key: str = ""  # alias for service_role / secret key
    supabase_publishable_key: str = ""  # publishable / anon key for frontend
    supabase_jwt_secret: str = ""  # fallback: used to verify Supabase Auth JWT tokens
    supabase_jwks_url: str = ""  # preferred: JWKS endpoint for JWT verification
    supabase_enabled: bool = False

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_web3forms_enabled(self) -> bool:
        return self.web3forms_enabled and bool(self.web3forms_access_key)

    @property
    def is_supabase_enabled(self) -> bool:
        return self.supabase_enabled and bool(self.supabase_url) and bool(self.supabase_secret_or_key)

    @property
    def supabase_secret_or_key(self) -> str:
        return self.supabase_secret_key or self.supabase_key

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
