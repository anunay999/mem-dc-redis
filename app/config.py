from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # General
    debug: bool = Field(default=False, alias="DEBUG")

    # Salesforce auth and endpoints
    salesforce_base_url: Optional[str] = Field(default=None, alias="SALESFORCE_BASE_URL")

    grant_type: str = Field(default="client_credentials", alias="GRANT_TYPE")
    client_id: Optional[str] = Field(default=None, alias="CLIENT_ID")
    client_secret: Optional[str] = Field(default=None, alias="CLIENT_SECRET")

    # Redis
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")
    
    google_api_key: Optional[str] = Field(default=None, alias="GOOGLE_API_KEY")

    dc_connector: Optional[str] = Field(default=None, alias="DC_INGEST_CONNECTOR")
    dc_dlo: Optional[str] = Field(default=None, alias="DC_DLO")

    # Data Cloud search parameters
    dc_vector_index_dlm: Optional[str] = Field(default=None, alias="DC_VECTOR_INDEX_DLM")
    dc_chunk_dlm: Optional[str] = Field(default=None, alias="DC_CHUNK_DLM")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached instance of Settings.

    - In local dev, loads variables from .env automatically.
    - In cloud (e.g., Heroku, Render, Vercel), reads directly from os.environ.
    - Environment variables always take precedence over .env.
    """
    return Settings()


