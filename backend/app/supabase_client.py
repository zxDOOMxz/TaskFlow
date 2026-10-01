from functools import lru_cache

from supabase import Client, create_client

from app.config import get_settings


@lru_cache
def get_supabase_client() -> Client:
    """Return a cached Supabase client initialized with the service_role key.

    The service_role key bypasses Row Level Security (RLS) and is intended
    for backend-server use only. Never expose it to the frontend.
    """
    settings = get_settings()
    if not settings.is_supabase_enabled:
        raise RuntimeError("Supabase integration is not configured")
    return create_client(settings.supabase_url, settings.supabase_key)


def get_supabase_anon_client() -> Client:
    """Return a Supabase client initialized with the anon/publishable key.

    Useful for operations that should respect RLS, e.g. public storage URLs.
    """
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise RuntimeError("Supabase anon key is not configured")
    return create_client(settings.supabase_url, settings.supabase_anon_key)
