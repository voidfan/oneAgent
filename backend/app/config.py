"""Application configuration using pydantic-settings."""
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Global application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "xAgent"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://xagent:xagent@db:5432/xagent"
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # LLM Configuration (新的 4 个核心配置项)
    LLM_PROVIDER: str = "openai"
    LLM_BASE_URL: Optional[str] = None
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4o"

    # Legacy LLM settings (保留兼容)
    DEFAULT_LLM_PROVIDER: str = "openai"

    # RAG / Vector Store
    CHROMA_PERSIST_DIR: str = "/data/chroma"

    # Token Budget
    MAX_TOKENS_PER_REQUEST: int = 4096
    MAX_CONTEXT_TOKENS: int = 128000
    TOKEN_BUDGET_WARNING: float = 0.8  # warn at 80% usage

    # Agent
    MAX_AGENT_STEPS: int = 50
    AGENT_TIMEOUT_SECONDS: int = 300
    MAX_CONCURRENT_AGENTS: int = 10

    # Security
    TOOL_SANDBOX_ENABLED: bool = True
    ALLOWED_TOOL_MODULES: list[str] = ["app.tools.builtin"]

    # Observability
    LOG_LEVEL: str = "INFO"
    ENABLE_TRACING: bool = True
    PROMETHEUS_ENABLED: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
