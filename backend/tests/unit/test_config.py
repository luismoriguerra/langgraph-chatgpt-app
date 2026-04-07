from app.config import Settings


class TestSettings:
    def test_default_values(self) -> None:
        s = Settings(openai_api_key="test-key", _env_file=None)  # type: ignore[call-arg]
        assert s.llm_model == "gpt-4o-mini"
        assert s.backend_port == 8000
        assert s.frontend_url == "http://localhost:4321"
        assert "chatgpt_app" in s.database_url

    def test_api_key_loaded(self) -> None:
        s = Settings(openai_api_key="sk-test-123", _env_file=None)  # type: ignore[call-arg]
        assert s.openai_api_key == "sk-test-123"
