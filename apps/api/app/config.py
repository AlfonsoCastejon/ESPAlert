from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
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
    ALLOWED_ORIGINS: str
    VAPID_PUBLIC_KEY: str
    VAPID_PRIVATE_KEY: SecretStr
    MQTT_BROKER_URL: str

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
