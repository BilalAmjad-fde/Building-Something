from supabase import client,create_client
from functools import lru_cache
from config import get_setting

setting = get_setting()

def get_supabase()->client:
    return create_client(supabase_key=setting.supabase_secret_key,supabase_url=setting.supabase_url)