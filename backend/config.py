"""
Configuration settings for ONYX Security Intelligence Platform
"""
import os
import logging
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "ONYX - Security Intelligence Platform"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=4, env="WORKERS")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # URLs
    backend_url: Optional[str] = Field(default=None, env="BACKEND_URL")
    frontend_url: str = Field(default="http://localhost:5173", env="FRONTEND_URL")
    api_base_url: Optional[str] = Field(default=None, env="API_BASE_URL")
    websocket_url: Optional[str] = Field(default=None, env="WEBSOCKET_URL")
    
    # Database
    mongodb_uri: str = Field(..., env="MONGODB_URI")
    database_name: str = Field(default="onyx", env="DATABASE_NAME")
    mongo_password: Optional[str] = Field(default=None, env="MONGO_PASSWORD")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=30, env="REFRESH_TOKEN_EXPIRE_DAYS")
    force_https: bool = Field(default=False, env="FORCE_HTTPS")
    
    # Authentication
    allow_registration: bool = Field(default=True, env="ALLOW_REGISTRATION")
    require_email_verification: bool = Field(default=True, env="REQUIRE_EMAIL_VERIFICATION")
    max_failed_login_attempts: int = Field(default=5, env="MAX_FAILED_LOGIN_ATTEMPTS")
    account_lockout_duration_minutes: int = Field(default=30, env="ACCOUNT_LOCKOUT_DURATION_MINUTES")
    
    # AI Configuration
    ai_provider: str = Field(default="openai", env="AI_PROVIDER")  # openai or gemini
    
    # OpenAI
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=2000, env="OPENAI_MAX_TOKENS")
    
    # Google Gemini
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-1.5-flash", env="GEMINI_MODEL")
    gemini_max_tokens: int = Field(default=2000, env="GEMINI_MAX_TOKENS")
    
    # Notifications
    slack_webhook_url: Optional[str] = Field(default=None, env="SLACK_WEBHOOK_URL")
    teams_webhook_url: Optional[str] = Field(default=None, env="TEAMS_WEBHOOK_URL")
    
    # Email Configuration
    email_enabled: bool = Field(default=False, env="EMAIL_ENABLED")
    smtp_server: Optional[str] = Field(default=None, env="SMTP_SERVER")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, env="SMTP_USERNAME") 
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, env="SMTP_USE_TLS")
    smtp_use_ssl: bool = Field(default=False, env="SMTP_USE_SSL")
    email_from: Optional[str] = Field(default=None, env="EMAIL_FROM")
    email_from_name: str = Field(default="ONYX Platform", env="EMAIL_FROM_NAME")
    
    # Email Provider Presets (for easy configuration)
    # Options: gmail, outlook, sendgrid, resend (for Render/cloud platforms)
    email_provider: Optional[str] = Field(default=None, env="EMAIL_PROVIDER")
    
    # Resend API Key (for HTTP-based email on cloud platforms like Render)
    resend_api_key: Optional[str] = Field(default=None, env="RESEND_API_KEY")
    
    slack_channel: str = Field(default="#dev-alerts", env="SLACK_CHANNEL")
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=3600, env="RATE_LIMIT_WINDOW")  # 1 hour
    rate_limit_per_minute: int = Field(default=1000, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_burst: int = Field(default=100, env="RATE_LIMIT_BURST")
    
    # CORS
    cors_origins: str = Field(
        default="", 
        env="CORS_ORIGINS"
    )
    allowed_origins: str = Field(default="", env="ALLOWED_ORIGINS")
    
    # Scanner configuration
    enable_semgrep: bool = Field(default=True, env="ENABLE_SEMGREP")
    enable_trivy: bool = Field(default=True, env="ENABLE_TRIVY")
    enable_gitleaks: bool = Field(default=True, env="ENABLE_GITLEAKS")
    enable_lynis: bool = Field(default=True, env="ENABLE_LYNIS")
    enable_bandit: bool = Field(default=True, env="ENABLE_BANDIT")
    enable_safety: bool = Field(default=True, env="ENABLE_SAFETY")
    scan_timeout: int = Field(default=300, env="SCAN_TIMEOUT")
    max_concurrent_scans: int = Field(default=3, env="MAX_CONCURRENT_SCANS")
    
    # Custom security rules
    custom_semgrep_rules_repo: Optional[str] = Field(default=None, env="CUSTOM_SEMGREP_RULES_REPO")
    custom_gitleaks_config: Optional[str] = Field(default=None, env="CUSTOM_GITLEAKS_CONFIG")
    
    # Trivy configuration
    trivy_cache_dir: str = Field(default="/tmp/trivy-cache", env="TRIVY_CACHE_DIR")
    trivy_db_update_interval: int = Field(default=24, env="TRIVY_DB_UPDATE_INTERVAL")  # hours
    
    # Redis
    redis_url: str = Field(default="redis://redis:6379", env="REDIS_URL")
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
    bandit_path: str = Field(default="bandit", env="BANDIT_PATH")
    safety_path: str = Field(default="safety", env="SAFETY_PATH")
    
    # Git operations
    git_clone_timeout: int = Field(default=300, env="GIT_CLONE_TIMEOUT")  # 5 minutes
    git_scan_timeout: int = Field(default=600, env="GIT_SCAN_TIMEOUT")   # 10 minutes
    
    # WebSocket
    websocket_heartbeat_interval: int = Field(default=30, env="WEBSOCKET_HEARTBEAT_INTERVAL")
    
    # Storage
    temp_dir: str = Field(default="/tmp/onyx", env="TEMP_DIR")
    cleanup_after_scan: bool = Field(default=True, env="CLEANUP_AFTER_SCAN")
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Convert CORS_ORIGINS string to list"""
        if not self.cors_origins:
            # In development, allow localhost origins. In production, this should be explicitly set.
            import os
            if os.getenv("ENVIRONMENT", "development").lower() == "production":
                # Production: Only allow specific origins (should be configured via CORS_ORIGINS env var)
                return ["https://onyx-platform.vercel.app"]
            return ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"]
        # Split by comma and clean up whitespace
        origins = [origin.strip() for origin in self.cors_origins.split(",")]
        return [origin for origin in origins if origin]  # Remove empty strings
    
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
