from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration for RELAY."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ------------------------------------------
    # Provider API Keys
    # ------------------------------------------

    groq_api_key: str | None = Field(
        default=None,
        validation_alias="GROQ_API_KEY",
    )

    gemini_api_key: str | None = Field(
        default=None,
        validation_alias="GEMINI_API_KEY",
    )

    openrouter_api_key: str | None = Field(
        default=None,
        validation_alias="OPENROUTER_API_KEY",
    )

    # ------------------------------------------
    # RELAY Configuration
    # ------------------------------------------

    provider_order: str = Field(
        default="groq,gemini,openrouter",
        validation_alias="RELAY_PROVIDER_ORDER",
    )

    timeout: float = Field(
        default=30.0,
        gt=0,
        validation_alias="RELAY_TIMEOUT",
    )

    max_attempts: int = Field(
        default=3,
        ge=1,
        validation_alias="RELAY_MAX_ATTEMPTS",
    )

    enable_failover: bool = Field(
        default=True,
        validation_alias="RELAY_ENABLE_FAILOVER",
    )

    environment: str = Field(
        default="development",
        validation_alias="RELAY_ENVIRONMENT",
    )

    # ------------------------------------------
    # Helpers
    # ------------------------------------------

    @property
    def providers(self) -> list[str]:
        """Return configured providers in priority order."""
        return [
            provider.strip().lower()
            for provider in self.provider_order.split(",")
            if provider.strip()
        ]

    def has_provider_key(self, provider: str) -> bool:
        """Check whether a provider has an API key configured."""
        keys = {
            "groq": self.groq_api_key,
            "gemini": self.gemini_api_key,
            "openrouter": self.openrouter_api_key,
        }

        return bool(keys.get(provider.lower()))


@lru_cache
def get_settings() -> Settings:
    """Return the cached RELAY settings instance."""
    return Settings()