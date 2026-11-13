import pytest

from assistant_core.config import Settings, load_settings
from assistant_core.errors import ConfigError


def test_settings_secret_not_leaked_in_repr():
    s = Settings(llm_api_key="super-secret-key-12345")
    assert "super-secret-key-12345" not in repr(s)
    assert s.llm_api_key == "super-secret-key-12345"


def test_settings_defaults():
    s = Settings()
    assert s.llm_provider == "stub"
    assert s.credit_rate_vnd == 450_000
    assert s.retake_multiplier == 1.5
    assert s.max_credits == 30
    assert s.log_level == "INFO"


def test_load_settings_missing_key_for_non_stub(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    with pytest.raises(ConfigError, match="LLM_API_KEY is required"):
        load_settings(env_file=None)
