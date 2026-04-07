from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/chatgpt_app"
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:4321"


settings = Settings()
