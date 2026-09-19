from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    bot_token: str = ""
    webapp_url: str = "http://localhost"
    database_url: str = "sqlite+aiosqlite:///./wathis.db"
    redis_url: str = "redis://redis:6379/0"
    youtube_api_key: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    vk_service_token: str = ""
    cors_origins: str = "*"
    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value):
        # BotHost may expose DATABASE_URL as an empty environment variable.
        # Treat an empty value as “not configured” and keep the local SQLite fallback.
        if value is None or not str(value).strip():
            return "sqlite+aiosqlite:///./wathis.db"
        return str(value).strip()

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
