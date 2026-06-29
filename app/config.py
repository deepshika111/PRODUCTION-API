from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings (BaseSettings):

    # LLM Configuration
    openai_api_key: str
    primary_model: str = "gpt-4o-mini"
    fallback_model: str = "gpt-4o-mini"

    # LangSmith
    langchain_tracing_v2: bool = True
    langchain_api_key: str = ""
    langchain_project: str = "production-api"

    # Application
    app_env: str = "development"
    log_level: str = "INFO"
    rate_limit: str = "20/minute"
    cache_ttl_seconds: int = 300
    max_retries: int = 3

    model_config = SettingsConfigDict (
        env_file = '.env',
        case_sensitive=False,
        extra="ignore",     

    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
