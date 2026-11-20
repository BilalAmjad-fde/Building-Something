from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    gemini_api_key:str
    gemini_api_model:str
    voyageai_api_key: str
    voyageai_model: str = "voyage-4"

    database_url:str
    supabase_url:str
    supabase_publishable_key:str
    supabase_secret_key:str

    adzuna_id:str
    adzuna_api_key:str
    adzuna_base_url:str="https://api.adzuna.com/v1/api/jobs"

    fetch_interval_hour:int = 6

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

@lru_cache
def get_setting()->Settings:
    return Settings()



    