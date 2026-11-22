from functools import lru_cache

from supabase import Client, create_client

from backend.app.config import get_setting


@lru_cache
def get_supabase() -> Client:
    setting = get_setting()
    return create_client(
        supabase_url=setting.supabase_url,
        supabase_key=setting.supabase_secret_key,
    )