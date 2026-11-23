from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    gemini_api_key:str
    gemini_api_model:str
    mistral_api_key: str
    mistral_model: str 

    database_url:str
    supabase_url:str
    supabase_publishable_key:str
    supabase_secret_key:str

    adzuna_id:str
    adzuna_api_key:str
    adzuna_base_url:str="https://api.adzuna.com/v1/api/jobs"
    adzuna_country_code: str = "us"

    fetch_interval_hour: int = Field(default=6, gt=0)
    celery_broker_url: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache
def get_setting() -> Settings:
    return Settings()



    