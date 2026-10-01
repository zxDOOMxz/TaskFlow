import httpx
from fastapi import HTTPException, status

from app.config import Settings, get_settings


class SupabaseAuthError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class SupabaseAuthClient:
    """Lightweight Python client for Supabase Auth REST endpoints.

    Replicates the behaviour of @supabase/server for Node.js so that a
    Python/FastAPI backend can create and authenticate users via Supabase Auth.
    """

    def __init__(self, settings: Settings = None):
        self.settings = settings or get_settings()
        if not self.settings.is_supabase_enabled:
            raise RuntimeError("Supabase integration is not configured")
        self.base_url = f"{self.settings.supabase_url}/auth/v1"
        self.headers = {
            "apikey": self.settings.supabase_publishable_key or self.settings.supabase_secret_or_key,
            "Authorization": f"Bearer {self.settings.supabase_secret_or_key}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, json: dict = None) -> dict:
        url = f"{self.base_url}{path}"
        try:
            response = httpx.request(
                method,
                url,
                headers=self.headers,
                json=json,
                timeout=20.0,
            )
            response.raise_for_status()
            return response.json() if response.text else {}
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text
            try:
                detail = exc.response.json().get("msg") or exc.response.json().get("message") or detail
            except Exception:
                pass
            raise SupabaseAuthError(detail, exc.response.status_code) from exc
        except httpx.RequestError as exc:
            raise SupabaseAuthError(f"Could not reach Supabase Auth: {exc}", 502) from exc

    def sign_up(self, email: str, password: str, user_metadata: dict = None) -> dict:
        """Create a new Supabase Auth user and return the session."""
        payload = {"email": email, "password": password}
        if user_metadata:
            payload["data"] = user_metadata
        return self._request("POST", "/signup", json=payload)

    def sign_in(self, email: str, password: str) -> dict:
        """Authenticate a user and return the session."""
        return self._request("POST", "/token?grant_type=password", json={"email": email, "password": password})

    def get_user(self, jwt_token: str) -> dict:
        """Return the Supabase user for a given access token."""
        headers = {
            **self.headers,
            "Authorization": f"Bearer {jwt_token}",
        }
        url = f"{self.base_url}/user"
        try:
            response = httpx.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise SupabaseAuthError(exc.response.text, exc.response.status_code) from exc
        except httpx.RequestError as exc:
            raise SupabaseAuthError(f"Could not reach Supabase Auth: {exc}", 502) from exc


def get_supabase_auth_client(settings: Settings = None) -> SupabaseAuthClient:
    return SupabaseAuthClient(settings)
