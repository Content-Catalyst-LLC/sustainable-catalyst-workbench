from functools import lru_cache
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Runtime settings for Sustainable Catalyst Workbench API.

    v0.7.3 keeps the provider stack intentionally small:
    disabled, gemini, deepseek, or openai.

    API key aliases are accepted so the same backend works locally, on Render,
    or behind WordPress-managed provider forwarding.
    """

    environment: str = Field(default="development", validation_alias=AliasChoices("SC_WORKBENCH_ENVIRONMENT", "SC_WORKBENCH_ENV"))
    backend_key: str = ""
    ai_provider: str = "disabled"

    openai_api_key: str = Field(default="", validation_alias=AliasChoices("SC_WORKBENCH_OPENAI_API_KEY", "OPENAI_API_KEY"))
    openai_model: str = "gpt-4.1-mini"

    gemini_api_key: str = Field(default="", validation_alias=AliasChoices("SC_WORKBENCH_GEMINI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"))
    gemini_model: str = "gemini-3.5-flash"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"

    deepseek_api_key: str = Field(default="", validation_alias=AliasChoices("SC_WORKBENCH_DEEPSEEK_API_KEY", "DEEPSEEK_API_KEY"))
    deepseek_model: str = "deepseek-v4-flash"
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_thinking: str = "disabled"
    deepseek_reasoning_effort: str = "high"

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
