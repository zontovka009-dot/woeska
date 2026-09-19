from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DATABASE_URL = "sqlite+aiosqlite:////app/data/wathis.db"

class Settings(BaseSettings):
    bot_token: str = ""
    webapp_url: str = "http://localhost"
    database_url: str = DEFAULT_DATABASE_URL
    redis_url: str = "redis://redis:6379/0"
    youtube_api_key: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    vk_service_token: str = ""
    cors_origins: str = "*"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
