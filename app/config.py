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
    redis_host: Optional[str] = Field(default=None, alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_username: Optional[str] = Field(default=None, alias="REDIS_USERNAME")
    redis_password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")

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


