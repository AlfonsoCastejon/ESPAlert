from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Variables obligatorias (sin valor por defecto)
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    ENV: Literal["development", "production"]
    DATABASE_URL: str
    REDIS_URL: str
    AEMET_API_KEY: SecretStr
    ALLOWED_ORIGINS: list[str] | str
    VAPID_PUBLIC_KEY: str
    VAPID_PRIVATE_KEY: SecretStr
    MQTT_BROKER_URL: str


@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
