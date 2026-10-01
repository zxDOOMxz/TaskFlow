from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.models import User

security = HTTPBearer(auto_error=False)


class SupabaseUser(BaseModel):
    id: UUID
    email: str
    raw: dict


class _JWKSClient:
    """Minimal JWKS client that caches keys for Supabase Auth JWT verification."""

    def __init__(self):
        self._jwks_data: Optional[dict] = None
        self._jwks_url: Optional[str] = None

    def _fetch_jwks(self, url: str) -> dict:
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        return response.json()

    def get_signing_key(self, token: str, settings: Settings) -> jwt.PyJWK:
        if not settings.supabase_jwks_url:
            raise RuntimeError("SUPABASE_JWKS_URL is not configured")

        # Refresh JWKS if URL changed or not loaded yet
        if self._jwks_data is None or self._jwks_url != settings.supabase_jwks_url:
            self._jwks_data = self._fetch_jwks(settings.supabase_jwks_url)
            self._jwks_url = settings.supabase_jwks_url

        # Find the key matching the token's kid
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            raise jwt.InvalidTokenError("Token has no kid header")

        for key in self._jwks_data.get("keys", []):
            if key.get("kid") == kid:
                return jwt.PyJWK(key)

        raise jwt.InvalidTokenError(f"No matching JWKS key found for kid={kid}")


_jwks_client = _JWKSClient()


def decode_supabase_token(token: str, settings: Settings) -> Optional[dict]:
    """Decode and verify a Supabase Auth JWT using JWKS or the fallback JWT secret."""
    # Prefer JWKS if configured
    if settings.supabase_jwks_url:
        try:
            signing_key = _jwks_client.get_signing_key(token, settings)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "EdDSA"],
                audience="authenticated",
                options={"verify_exp": True},
            )
            return payload
        except jwt.InvalidTokenError:
            return None
        except Exception:
            return None

    # Fallback to HS256 with the JWT secret
    if not settings.supabase_jwt_secret:
        return None
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
            options={"verify_exp": True},
        )
        return payload
    except jwt.InvalidTokenError:
        return None


def get_supabase_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    settings: Settings = Depends(get_settings),
) -> Optional[SupabaseUser]:
    """Dependency that validates a Supabase JWT and returns the user info."""
    if not credentials:
        return None
    payload = decode_supabase_token(credentials.credentials, settings)
    if not payload:
        return None
    user_id = payload.get("sub")
    email = payload.get("email")
    if not user_id or not email:
        return None
    return SupabaseUser(id=UUID(user_id), email=email, raw=payload)


def require_supabase_user(
    supabase_user: Optional[SupabaseUser] = Depends(get_supabase_user),
) -> SupabaseUser:
    if not supabase_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Supabase token",
        )
    return supabase_user
