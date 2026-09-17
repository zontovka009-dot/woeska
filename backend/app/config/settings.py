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
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
