import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./chess_coach.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET: str = "placeholder_secret_for_skeleton"
    JWT_ALGORITHM: str = "HS256"
    
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    GOOGLE_CLOUD_PROJECT: str = ""
    GOOGLE_CLOUD_LOCATION: str = ""
    AI_MODEL_NAME: str = ""

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        extra='ignore'
    )

settings = Settings()
