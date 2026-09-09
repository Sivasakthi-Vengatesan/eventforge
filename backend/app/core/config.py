import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "EventForge"
    API_V1_PREFIX: str = "/api/v1"
    
    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite+aiosqlite:///./eventforge.db"
    )
    
    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    USE_EMBEDDED_STREAM_FALLBACK: bool = True
    
    # Webhook Secrets
    WEBHOOK_SECRET_STRIPE: str = os.getenv("WEBHOOK_SECRET_STRIPE", "whsec_stripe_test_secret_38472948")
    WEBHOOK_SECRET_RAZORPAY: str = os.getenv("WEBHOOK_SECRET_RAZORPAY", "rzp_sec_razorpay_test_98372184")
    WEBHOOK_SECRET_GITHUB: str = os.getenv("WEBHOOK_SECRET_GITHUB", "gh_sec_github_test_84729184")
    WEBHOOK_SECRET_GENERIC: str = os.getenv("WEBHOOK_SECRET_GENERIC", "gen_sec_generic_test_19284729")

    GITHUB_WEBHOOK_SECRET: str = os.getenv("GITHUB_WEBHOOK_SECRET", "gh_sec_github_test_84729184")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_stripe_test_secret_38472948")
    RAZORPAY_WEBHOOK_SECRET: str = os.getenv("RAZORPAY_WEBHOOK_SECRET", "rzp_sec_razorpay_test_98372184")
    
    # Queue & Worker Settings
    STREAM_NAME: str = "events:incoming"
    CONSUMER_GROUP: str = "event-workers"
    WORKER_COUNT: int = 4
    MIN_WORKERS: int = 2
    MAX_WORKERS: int = 8
    MAX_RETRIES: int = 5
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
    CORS_ORIGINS: List[str] = ["*"]

settings = Settings()

