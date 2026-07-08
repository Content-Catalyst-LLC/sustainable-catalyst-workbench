from functools import lru_cache
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Runtime settings for Sustainable Catalyst Workbench API.

    The backend accepts both SC_WORKBENCH_OPENAI_API_KEY and OPENAI_API_KEY.
    This keeps local .env usage simple while still allowing prefixed production
    variables on hosts such as Render, Railway, Fly.io, or a VPS.
    """

    environment: str = Field(default="development", validation_alias=AliasChoices("SC_WORKBENCH_ENVIRONMENT", "SC_WORKBENCH_ENV"))
    backend_key: str = ""
    ai_provider: str = "disabled"
    openai_api_key: str = Field(default="", validation_alias=AliasChoices("SC_WORKBENCH_OPENAI_API_KEY", "OPENAI_API_KEY"))
    openai_model: str = "gpt-4.1-mini"
    max_output_tokens: int = 1000
    temperature: float = 0.2
    allow_wordpress_provider_key: bool = True
    scope_gate: bool = True
    cors_origins: str = "http://localhost:8888,http://127.0.0.1:8888,https://sustainablecatalyst.com"

    model_config = SettingsConfigDict(env_prefix="SC_WORKBENCH_", env_file=".env", extra="ignore")

    @property
    def origins(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()
