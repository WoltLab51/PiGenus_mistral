"""
Configuration settings for PiGenus using Pydantic Settings.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """
    PiGenus configuration settings.
    Loads from environment variables or .env file.
    """

    # Database
    database_url: str = Field(
        default="sqlite:///pigenus.db",
        env="DATABASE_URL",
        description="Database connection URL (SQLite or PostgreSQL)"
    )

    # Security
    secret_key: str = Field(
        ...,
        env="SECRET_KEY",
        description="Secret key for JWT token signing"
    )
    algorithm: str = Field(
        default="HS256",
        env="ALGORITHM",
        description="JWT signing algorithm"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        env="ACCESS_TOKEN_EXPIRE_MINUTES",
        ge=1,
        description="JWT token expiration time in minutes"
    )

    # API
    debug: bool = Field(
        default=False,
        env="DEBUG",
        description="Enable debug mode (development only)"
    )
    host: str = Field(
        default="0.0.0.0",
        env="HOST",
        description="API server host"
    )
    port: int = Field(
        default=8000,
        env="PORT",
        ge=1,
        le=65535,
        description="API server port"
    )

    # Worker
    worker_lease_timeout: int = Field(
        default=60,
        env="WORKER_LEASE_TIMEOUT",
        ge=10,
        description="Timeout in seconds for worker job lease"
    )

    # Scheduler
    nightly_jobs_hour: int = Field(
        default=3,
        env="NIGHTLY_JOBS_HOUR",
        ge=0,
        le=23,
        description="Hour of the day to run nightly jobs (UTC)"
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
