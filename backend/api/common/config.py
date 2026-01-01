import os
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class DatabaseSettings(BaseSettings):
    """Database configuration."""
    url: str = Field(default="sqlite+aiosqlite:///./chess_coach.db", alias="DATABASE_URL")

class RedisSettings(BaseSettings):
    """Redis configuration."""
    url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

class AuthSettings(BaseSettings):
    """Authentication configuration."""
    jwt_secret: str = Field(default="placeholder_secret_for_skeleton", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")

    @validator('jwt_secret')
    def validate_jwt_secret(cls, v):
        if v == "placeholder_secret_for_skeleton":
            import warnings
            warnings.warn("Using placeholder JWT secret. Set JWT_SECRET environment variable in production.")
        return v

class AISettings(BaseSettings):
    """AI service configuration."""
    google_application_credentials: Optional[str] = Field(default=None, alias="GOOGLE_APPLICATION_CREDENTIALS")
    google_cloud_project: Optional[str] = Field(default=None, alias="GOOGLE_CLOUD_PROJECT")
    google_cloud_location: Optional[str] = Field(default=None, alias="GOOGLE_CLOUD_LOCATION")
    model_name: Optional[str] = Field(default=None, alias="AI_MODEL_NAME")

class Settings(BaseSettings):
    """Main application settings."""
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    auth: AuthSettings = AuthSettings()
    ai: AISettings = AISettings()

    # Convenience properties
    @property
    def DATABASE_URL(self) -> str:
        return self.database.url

    @property
    def REDIS_URL(self) -> str:
        return self.redis.url

    @property
    def JWT_SECRET(self) -> str:
        return self.auth.jwt_secret

    @property
    def JWT_ALGORITHM(self) -> str:
        return self.auth.jwt_algorithm

    @property
    def GOOGLE_APPLICATION_CREDENTIALS(self) -> Optional[str]:
        return self.ai.google_application_credentials

    @property
    def GOOGLE_CLOUD_PROJECT(self) -> Optional[str]:
        return self.ai.google_cloud_project

    @property
    def GOOGLE_CLOUD_LOCATION(self) -> Optional[str]:
        return self.ai.google_cloud_location

    @property
    def AI_MODEL_NAME(self) -> Optional[str]:
        return self.ai.model_name

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_nested_delimiter="__",
        extra='ignore'
    )

settings = Settings()
