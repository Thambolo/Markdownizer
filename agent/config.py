"""Configuration management for Markdownizer agent."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    """Default fallbacks if .env does not specify"""

    # OpenAI Configuration (Optional - will use ConnectOnion free tier as fallback)
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    
    # Model Preferences
    use_connectonion_free: bool = True  # Try ConnectOnion's free tier first
    connectonion_model: str = "co/gpt-4o-mini"  # Free ConnectOnion model

    # ConnectOnion Configuration (Optional - for platform features)
    openonion_api_key: str | None = None
    connectonion_api_key: str | None = None
    agent_email: str | None = None

    # Server Configuration
    server_host: str = "127.0.0.1"
    server_port: int = 5050
    server_reload: bool = True

    # Playwright Configuration
    playwright_headless: bool = True
    playwright_timeout: int = 30  # seconds (will be converted to ms in code)

    # HTTP Client Configuration
    http_timeout: int = 15  # seconds
    http_max_retries: int = 3
    http_user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # Comparison Configuration
    score_threshold: float = 0.05  # Tie threshold
    min_content_length: int = 100  # Minimum content length (chars)
    max_content_length: int = 50000  # Maximum content length (chars)


# Global settings instance
settings = Settings()
