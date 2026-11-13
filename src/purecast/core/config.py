"""Application configuration management using pydantic-settings."""

import json
from functools import lru_cache
from typing import Annotated

from pydantic import BeforeValidator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_cors_origins(v: object) -> list[str]:
    if isinstance(v, str):
        if v.startswith("[") and v.endswith("]"):
            return json.loads(v)
        return [i.strip() for i in v.split(",") if i.strip()]
    if isinstance(v, list):
        return [str(i) for i in v]
    return ["http://localhost:3000", "http://localhost:5173"]


class Settings(BaseSettings):
    """Core application settings loaded from environment and .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "purecast"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-64"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://purecast:purecast_dev@localhost:5432/purecast"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL_SECONDS: int = 300

    # MQTT
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: str = "purecast_ingestor"
    MQTT_PASSWORD: str = "change-me-in-production"
    MQTT_TOPIC_PREFIX: str = "purecast"

    # Auth / JWT
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Argon2
    ARGON2_TIME_COST: int = 2
    ARGON2_MEMORY_COST: int = 19456
    ARGON2_PARALLELISM: int = 1

    # CORS
    CORS_ORIGINS: Annotated[list[str], BeforeValidator(_parse_cors_origins)] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10

    # Observability
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"
    OTEL_SERVICE_NAME: str = "purecast-api"
    PROMETHEUS_PORT: int = 9090

    # Testing flag
    TESTING: bool = False


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
