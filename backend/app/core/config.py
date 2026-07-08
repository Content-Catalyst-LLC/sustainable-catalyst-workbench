import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    ai_provider: str = os.getenv("SC_WORKBENCH_AI_PROVIDER", "disabled").strip().lower()
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "").strip()
    openai_model: str = os.getenv("SC_WORKBENCH_OPENAI_MODEL", "gpt-4.1-mini").strip()
    max_output_tokens: int = int(os.getenv("SC_WORKBENCH_MAX_OUTPUT_TOKENS", "900"))
    temperature: float = float(os.getenv("SC_WORKBENCH_TEMPERATURE", "0.2"))
    backend_key: str = os.getenv("SC_WORKBENCH_BACKEND_KEY", "").strip()
    allow_wordpress_provider_key: bool = os.getenv("SC_WORKBENCH_ALLOW_WORDPRESS_PROVIDER_KEY", "true").strip().lower() in {"1", "true", "yes"}

settings = Settings()
