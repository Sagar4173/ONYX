"""
Configuration settings for SecureDevOps Platform
"""
import os
import logging
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "SecureDevOps AI Platform"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=4, env="WORKERS")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Database
    mongodb_uri: str = Field(..., env="MONGODB_URI")
    database_name: str = Field(default="securedevops", env="DATABASE_NAME")
    mongo_password: Optional[str] = Field(default=None, env="MONGO_PASSWORD")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    force_https: bool = Field(default=False, env="FORCE_HTTPS")
    
    # OpenAI
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=2000, env="OPENAI_MAX_TOKENS")
    
    # Notifications
    slack_webhook_url: Optional[str] = Field(default=None, env="SLACK_WEBHOOK_URL")
    teams_webhook_url: Optional[str] = Field(default=None, env="TEAMS_WEBHOOK_URL")
    slack_channel: str = Field(default="#dev-alerts", env="SLACK_CHANNEL")
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=3600, env="RATE_LIMIT_WINDOW")  # 1 hour
    rate_limit_per_minute: int = Field(default=1000, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_burst: int = Field(default=100, env="RATE_LIMIT_BURST")
    
    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"], 
        env="CORS_ORIGINS"
    )
    allowed_origins: str = Field(default="http://localhost:3000,http://localhost:8080", env="ALLOWED_ORIGINS")
    
    # Scanner configuration
    enable_semgrep: bool = Field(default=False, env="ENABLE_SEMGREP")
    enable_trivy: bool = Field(default=False, env="ENABLE_TRIVY")
    enable_gitleaks: bool = Field(default=False, env="ENABLE_GITLEAKS")
    enable_lynis: bool = Field(default=False, env="ENABLE_LYNIS")
    scan_timeout: int = Field(default=300, env="SCAN_TIMEOUT")
    max_concurrent_scans: int = Field(default=3, env="MAX_CONCURRENT_SCANS")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_db: int = Field(default=0, env="REDIS_DB")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/app.log", env="LOG_FILE")
    log_max_size: int = Field(default=10*1024*1024, env="LOG_MAX_SIZE")  # 10MB
    log_backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    # Scanner paths
    semgrep_path: str = Field(default="semgrep", env="SEMGREP_PATH")
    trivy_path: str = Field(default="trivy", env="TRIVY_PATH")
    gitleaks_path: str = Field(default="gitleaks", env="GITLEAKS_PATH")
    lynis_path: str = Field(default="lynis", env="LYNIS_PATH")
    
    # Git operations
    git_clone_timeout: int = Field(default=300, env="GIT_CLONE_TIMEOUT")  # 5 minutes
    git_scan_timeout: int = Field(default=600, env="GIT_SCAN_TIMEOUT")   # 10 minutes
    
    # WebSocket
    websocket_heartbeat_interval: int = Field(default=30, env="WEBSOCKET_HEARTBEAT_INTERVAL")
    
    # Storage
    temp_dir: str = Field(default="/tmp/securedevops", env="TEMP_DIR")
    cleanup_after_scan: bool = Field(default=True, env="CLEANUP_AFTER_SCAN")
    
    model_config = {"extra": "ignore", "env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": False}


def get_log_level() -> int:
    """Convert string log level to logging constant"""
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return level_map.get(settings.log_level.upper(), logging.INFO)


# Global settings instance
settings = Settings()
