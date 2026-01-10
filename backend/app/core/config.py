"""Application configuration using Pydantic Settings"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_name: str = "Fraud Detection API"
    app_version: str = "2.0.0"
    debug: bool = False

    # Database
    database_url: str = "sqlite:///./fraud_detection.db"

    # API
    api_v1_prefix: str = "/api/v1"

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # ML Model paths
    model_path: str = "models/fraud_detector.pkl"
    scaler_path: str = "models/scaler.pkl"

    # Logging
    log_level: str = "INFO"

    # JWT Authentication
    secret_key: str = "your-super-secret-key-change-in-production-2024"
    refresh_secret_key: str = "your-refresh-secret-key-change-in-production-2024"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Rate Limiting
    rate_limit_per_minute: int = 60  # requests per minute

    # Email Settings (for password reset and alerts)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = "noreply@frauddetection.com"
    email_from_name: str = "Fraud Detection System"

    # Redis Settings (for caching)
    redis_url: str = "redis://localhost:6379"
    redis_enabled: bool = False

    # 2FA Settings
    totp_issuer: str = "FraudDetectionML"

    # File Upload Settings
    max_upload_size_mb: int = 10
    allowed_extensions: str = "csv,xlsx"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def allowed_extensions_list(self) -> List[str]:
        """Parse allowed extensions from comma-separated string"""
        return [ext.strip() for ext in self.allowed_extensions.split(",")]

    @property
    def max_upload_size(self) -> int:
        """Get max upload size in bytes"""
        return self.max_upload_size_mb * 1024 * 1024

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
