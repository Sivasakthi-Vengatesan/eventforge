import os
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "EventForge"
    API_V1_PREFIX: str = "/api/v1"
    
    # Database Configuration (PostgreSQL primary, SQLite for unit tests)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://postgres:postgres@localhost:5432/eventforge" if os.getenv("ENV") == "production" else "sqlite+aiosqlite:///./eventforge.db"
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_db_url(cls, v: str) -> str:
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgresql://") and not v.startswith("postgresql+"):
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v
    
    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    USE_EMBEDDED_STREAM_FALLBACK: bool = os.getenv("USE_EMBEDDED_STREAM_FALLBACK", "true").lower() in ["true", "1", "yes"]

    
    # Canonical Webhook Secrets (with backward compatible fallback)
    WEBHOOK_SECRET_STRIPE: str = os.getenv("WEBHOOK_SECRET_STRIPE") or os.getenv("STRIPE_WEBHOOK_SECRET") or "whsec_stripe_test_secret_38472948"
    WEBHOOK_SECRET_RAZORPAY: str = os.getenv("WEBHOOK_SECRET_RAZORPAY") or os.getenv("RAZORPAY_WEBHOOK_SECRET") or "rzp_sec_razorpay_test_98372184"
    WEBHOOK_SECRET_GITHUB: str = os.getenv("WEBHOOK_SECRET_GITHUB") or os.getenv("GITHUB_WEBHOOK_SECRET") or "gh_sec_github_test_84729184"
    WEBHOOK_SECRET_GENERIC: str = os.getenv("WEBHOOK_SECRET_GENERIC", "gen_sec_generic_test_19284729")

    @property
    def GITHUB_WEBHOOK_SECRET(self) -> str:
        return self.WEBHOOK_SECRET_GITHUB

    @property
    def STRIPE_WEBHOOK_SECRET(self) -> str:
        return self.WEBHOOK_SECRET_STRIPE

    @property
    def RAZORPAY_WEBHOOK_SECRET(self) -> str:
        return self.WEBHOOK_SECRET_RAZORPAY
    
    # Queue & Worker Settings
    STREAM_NAME: str = "events:incoming"
    CONSUMER_GROUP: str = "event-workers"
    WORKER_COUNT: int = int(os.getenv("WORKER_COUNT", "4"))
    MIN_WORKERS: int = 2
    MAX_WORKERS: int = 8
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "5"))
    BASE_RETRY_DELAY_SEC: float = 1.0

    # Adaptive Thresholds
    QUEUE_PRESSURE_THRESHOLD: int = 50
    P95_LATENCY_THRESHOLD: float = 400.0
    RATE_LIMIT_THRESHOLD: float = 0.15
    RECOVERY_WINDOW: float = 8.0
    
    # Mock External Service Fault Injection Defaults
    MOCK_SUCCESS_RATE: float = 0.90
    MOCK_TIMEOUT_RATE: float = 0.05
    MOCK_SERVER_ERROR_RATE: float = 0.05
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        return [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173"
        ]

settings = Settings()


