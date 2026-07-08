import os
from dataclasses import dataclass


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    env: str = os.getenv("SC_WORKBENCH_ENV", "local")
    allowed_origins: list[str] = None
    enable_live_ai: bool = os.getenv("SC_ENABLE_LIVE_AI", "false").lower() == "true"
    openai_api_key: str = os.getenv("SC_OPENAI_API_KEY", "")
    database_url: str = os.getenv("DATABASE_URL", "postgresql://scwb:scwb@localhost:5433/scwb")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6380/0")

    def __post_init__(self):
        if self.allowed_origins is None:
            object.__setattr__(self, "allowed_origins", _split_csv(os.getenv(
                "SC_ALLOWED_ORIGINS",
                "http://localhost:8888,http://127.0.0.1:8888,https://sustainablecatalyst.com",
            )))


settings = Settings()
