"""
ChargeMesh — Application Configuration
All settings loaded from environment variables with sensible defaults.
Secret settings (DATABASE_URL, DB_PASSWORD, JWT_SECRET_KEY, ENCRYPTION_KEY)
have no defaults and MUST be provided via environment variables or .env file.
"""

from functools import lru_cache
from typing import Literal, List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "ChargeMesh"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    FRONTEND_URL: str = "http://localhost:3000"

    # CORS — comma-separated list of allowed origins; defaults to localhost only
    CORS_ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # Database — no default; must be set in environment
    DATABASE_URL: str
    DB_PASSWORD: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # MQTT
    MQTT_BROKER_URL: str = "mqtt://localhost:1883"

    # JWT Auth — no default for secret; must be set in environment
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Encryption (Fernet key for sensitive tokens at rest) — no default; must be set in environment
    ENCRYPTION_KEY: str

    # Maps
    MAPBOX_ACCESS_TOKEN: str = ""
    GOOGLE_MAPS_API_KEY: str = ""

    # Integration modes
    OEM_MODE: Literal["mock", "live"] = "mock"
    CHARGING_NETWORK_MODE: Literal["mock", "live"] = "mock"

    # Push notifications
    FCM_SERVER_KEY: str = ""

    # Email
    EMAIL_BACKEND: Literal["console", "smtp"] = "console"

    # OCPP Server
    OCPP_SERVER_HOST: str = "0.0.0.0"
    OCPP_SERVER_PORT: int = 9000

    # Thermal thresholds (Celsius)
    THERMAL_WARNING_THRESHOLD: float = 42.0
    THERMAL_CRITICAL_THRESHOLD: float = 48.0

    # Dispatch configuration defaults
    DISPATCH_SOC_THRESHOLD: float = 25.0   # % SoC below which dispatch evaluates
    DISPATCH_SAFETY_BUFFER_KM: float = 10.0  # extra km buffer in charge-to-complete

    # Rate limiting
    RATE_LIMIT_DRIVER: int = 30       # req/min
    RATE_LIMIT_FLEET_MANAGER: int = 120  # req/min
    RATE_LIMIT_TELEMETRY: int = 1000  # req/min

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_db_url(cls, v: str) -> str:
        # Ensure asyncpg driver is specified
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
