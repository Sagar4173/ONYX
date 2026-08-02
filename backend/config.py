"""
Configuration settings for ONYX Security Intelligence Platform
"""
import logging
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


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
    secret_key: str = Field(..., env="SECRET_KEY", min_length=32)
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
    # Supported providers: auto, ollama, openai, gemini
    # auto = tries ollama → gemini → openai in order
    ai_provider: str = Field(default="auto", env="AI_PROVIDER")
    
    # OpenAI
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=2000, env="OPENAI_MAX_TOKENS")
    
    # Google Gemini
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-1.5-flash", env="GEMINI_MODEL")
    gemini_max_tokens: int = Field(default=2000, env="GEMINI_MAX_TOKENS")

    # Ollama (self-hosted local LLM)
    ai_local_base_url: str = Field(default="http://ollama:11434/v1", env="AI_LOCAL_BASE_URL")
    ai_local_model: str = Field(default="qwen2.5-coder:7b", env="AI_LOCAL_MODEL")
    ai_local_timeout: int = Field(default=120, env="AI_LOCAL_TIMEOUT")
    
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
    # Options: gmail, outlook, sendgrid, custom
    email_provider: Optional[str] = Field(default=None, env="EMAIL_PROVIDER")
    
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
    
    # ============================================================================
    # Scanner Configuration - Core Scanners (Always Available)
    # ============================================================================
    enable_semgrep: bool = Field(default=True, env="ENABLE_SEMGREP")
    enable_bandit: bool = Field(default=True, env="ENABLE_BANDIT")
    enable_safety: bool = Field(default=True, env="ENABLE_SAFETY")
    enable_gitleaks: bool = Field(default=True, env="ENABLE_GITLEAKS")
    
    # ============================================================================
    # Scanner Configuration - Optional Scanners (Require External Installation)
    # ============================================================================
    # These scanners require external tools to be installed on the system.
    # Set to True only if the corresponding tool is available.
    enable_trivy: bool = Field(default=False, env="ENABLE_TRIVY")  # Container scanning
    enable_lynis: bool = Field(default=False, env="ENABLE_LYNIS")  # Infrastructure audit
    enable_zap: bool = Field(default=False, env="ENABLE_ZAP")      # DAST - requires ZAP daemon
    enable_nuclei: bool = Field(default=False, env="ENABLE_NUCLEI")  # DAST - requires nuclei binary
    enable_codeql: bool = Field(default=False, env="ENABLE_CODEQL")  # SAST - requires CodeQL CLI
    enable_checkov: bool = Field(default=False, env="ENABLE_CHECKOV")  # IaC scanning
    
    # Scan settings
    scan_timeout: int = Field(default=300, env="SCAN_TIMEOUT")
    max_concurrent_scans: int = Field(default=3, env="MAX_CONCURRENT_SCANS")
    
    # Custom security rules
    custom_semgrep_rules_repo: Optional[str] = Field(default=None, env="CUSTOM_SEMGREP_RULES_REPO")
    custom_gitleaks_config: Optional[str] = Field(default=None, env="CUSTOM_GITLEAKS_CONFIG")
    
    # Trivy configuration (only used if enable_trivy=True)
    trivy_cache_dir: str = Field(default="/tmp/trivy-cache", env="TRIVY_CACHE_DIR")
    trivy_db_update_interval: int = Field(default=24, env="TRIVY_DB_UPDATE_INTERVAL")  # hours
    
    # Redis (Planned - not yet implemented, reserved for future caching)
    redis_url: str = Field(default="redis://redis:6379", env="REDIS_URL")
    redis_db: int = Field(default=0, env="REDIS_DB")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/app.log", env="LOG_FILE")
    log_max_size: int = Field(default=10*1024*1024, env="LOG_MAX_SIZE")  # 10MB
    log_backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    # Scanner paths (for optional scanners)
    semgrep_path: str = Field(default="semgrep", env="SEMGREP_PATH")
    trivy_path: str = Field(default="trivy", env="TRIVY_PATH")
    gitleaks_path: str = Field(default="gitleaks", env="GITLEAKS_PATH")
    lynis_path: str = Field(default="lynis", env="LYNIS_PATH")
    zap_api_url: str = Field(default="http://localhost:8080", env="ZAP_API_URL")
    nuclei_path: str = Field(default="nuclei", env="NUCLEI_PATH")
    codeql_path: str = Field(default="codeql", env="CODEQL_PATH")
    bandit_path: str = Field(default="bandit", env="BANDIT_PATH")
    safety_path: str = Field(default="safety", env="SAFETY_PATH")
    
    # Git operations
    git_clone_timeout: int = Field(default=300, env="GIT_CLONE_TIMEOUT")  # 5 minutes
    git_scan_timeout: int = Field(default=600, env="GIT_SCAN_TIMEOUT")   # 10 minutes

    # Webhooks
    webhook_secret: Optional[str] = Field(default=None, env="WEBHOOK_SECRET")
    
    # Auto-Fix PRs
    auto_fix_branch_prefix: str = Field(default="onyx-auto-fix/", env="AUTO_FIX_BRANCH_PREFIX")
    auto_fix_pr_title_prefix: str = Field(default="[ONYX Auto-Fix] ", env="AUTO_FIX_PR_TITLE_PREFIX")
    auto_fix_token: Optional[str] = Field(default=None, env="AUTO_FIX_TOKEN")
    
    # WebSocket
    websocket_heartbeat_interval: int = Field(default=30, env="WEBSOCKET_HEARTBEAT_INTERVAL")
    
    # Monitoring
    sentry_dsn: str = Field(default="", env="SENTRY_DSN")
    enable_prometheus: bool = Field(default=True, env="ENABLE_PROMETHEUS")

    # Storage
    temp_dir: str = Field(default="/tmp/onyx", env="TEMP_DIR")
    cleanup_after_scan: bool = Field(default=True, env="CLEANUP_AFTER_SCAN")
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Convert CORS_ORIGINS string to list"""
        if self.cors_origins and self.cors_origins.strip():
            origins = [origin.strip() for origin in self.cors_origins.split(",")]
            return [origin for origin in origins if origin]
        if self.environment.lower() == "production":
            return []  # Configure CORS_ORIGINS or ALLOWED_ORIGINS env var for production
        return ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"]
    
    def validate_ai_config(self) -> tuple[bool, str]:
        """
        Validate that the selected AI provider has a valid API key configured.
        Returns (is_valid, message) tuple.
        """
        if self.ai_provider == "openai":
            if not self.openai_api_key:
                return False, "OPENAI_API_KEY is required when ai_provider=openai"
            if self.openai_api_key.startswith("sk-") and len(self.openai_api_key) > 20:
                return True, "OpenAI configuration valid"
            return False, "OPENAI_API_KEY appears to be invalid format"
        elif self.ai_provider == "gemini":
            if not self.gemini_api_key:
                return False, "GEMINI_API_KEY is required when ai_provider=gemini"
            if len(self.gemini_api_key) > 10:
                return True, "Gemini configuration valid"
            return False, "GEMINI_API_KEY appears to be invalid format"
        elif self.ai_provider == "ollama":
            return True, "Ollama local AI configured"
        elif self.ai_provider == "auto":
            return True, "Auto-detecting AI provider (ollama → gemini → openai)"
        else:
            return False, f"Unknown AI provider: {self.ai_provider}. Use 'auto', 'ollama', 'openai', or 'gemini'"
    
    @property
    def ai_available(self) -> bool:
        """Check if AI functionality is properly configured"""
        if self.ai_provider in ("auto", "ollama"):
            return True
        is_valid, _ = self.validate_ai_config()
        return is_valid
    
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


def validate_settings_on_startup():
    """
    Validate critical settings on application startup.
    Logs warnings for missing optional but recommended settings.
    """
    logger = logging.getLogger(__name__)
    
    # Validate AI configuration
    is_valid, message = settings.validate_ai_config()
    if not is_valid:
        logger.warning(f"⚠️ AI Configuration Issue: {message}")
        logger.warning("⚠️ AI-powered features (remediation, analysis) will be unavailable.")
    else:
        logger.info(f"✅ AI Configuration: {message}")
    
    # Check for fallback AI provider
    has_openai = settings.openai_api_key and len(settings.openai_api_key) > 10
    has_gemini = settings.gemini_api_key and len(settings.gemini_api_key) > 10
    
    if settings.ai_provider in ("auto", "ollama"):
        logger.info(f"✅ Ollama local AI configured at {settings.ai_local_base_url} (model: {settings.ai_local_model})")
    if has_openai and has_gemini:
        logger.info("ℹ️ Both OpenAI and Gemini available as fallback")
    elif has_openai or has_gemini:
        logger.info("ℹ️ One API-based fallback provider available")
    if not has_openai and not has_gemini and settings.ai_provider not in ("auto", "ollama"):
        logger.warning("⚠️ No AI provider configured - AI features disabled")
    
    # Check email configuration
    if settings.email_enabled:
        if not settings.smtp_server:
            logger.warning("⚠️ EMAIL_ENABLED=true but SMTP_SERVER not configured")
    
    return is_valid


# Global settings instance
settings = Settings()

# Validate settings on import (warnings logged)
try:
    validate_settings_on_startup()
except Exception as e:
    logging.getLogger(__name__).error(f"Settings validation error: {e}")
