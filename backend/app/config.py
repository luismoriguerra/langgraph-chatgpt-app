from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_env_file = PROJECT_ROOT / ".env" if (PROJECT_ROOT / ".env").exists() else None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_env_file) if _env_file else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/chatgpt_app"
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:4321"


settings = Settings()
