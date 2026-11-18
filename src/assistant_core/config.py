import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from assistant_core.errors import ConfigError


class Settings(BaseModel):
    data_dir: Path = Path("data")
    llm_provider: str = "stub"
    llm_api_key: str | None = Field(default=None, repr=False)
    llm_timeout_s: float = 5.0
    credit_rate_vnd: int = 450_000
    retake_multiplier: float = 1.5
    max_credits: int = 30
    log_level: str = "INFO"
    llm_model: str = "llama3.2"
    llm_base_url: str | None = None
    kb_dir: Path = Path("data/kb")
    retrieval_kind: str = "bm25"
    retrieval_min_score: float = 2.0
    prompt_version: str = "answer_v1"
    api_admin_key: str | None = Field(default=None, repr=False)
    weather_url: str = "https://api.open-meteo.com/v1/forecast"
    weather_timeout_s: float = 3.0
    campus_lat: float = 10.7626
    campus_lon: float = 106.6822
    rate_limit_per_min: int = 30
    database_url: str = "sqlite:///assistant.db"
    session_salt: str = Field(default="dev-salt", repr=False)


def load_settings(env_file: str | None = ".env") -> Settings:
    if env_file:
        load_dotenv(env_file, override=False)
    s = Settings(
        data_dir=Path(os.getenv("ASSISTANT_DATA_DIR", "data")),
        llm_provider=os.getenv("LLM_PROVIDER", "stub"),
        llm_api_key=os.getenv("LLM_API_KEY") or None,
        llm_timeout_s=float(os.getenv("LLM_TIMEOUT_S", "5")),
        credit_rate_vnd=int(os.getenv("CREDIT_RATE_VND", "450000")),
        retake_multiplier=float(os.getenv("RETAKE_MULTIPLIER", "1.5")),
        max_credits=int(os.getenv("MAX_CREDITS", "30")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        llm_model=os.getenv("LLM_MODEL", "llama3.2"),
        llm_base_url=os.getenv("LLM_BASE_URL") or None,
        kb_dir=Path(os.getenv("KB_DIR", "data/kb")),
        retrieval_kind=os.getenv("RETRIEVAL_KIND", "bm25"),
        retrieval_min_score=float(os.getenv("RETRIEVAL_MIN_SCORE", "2.0")),
        prompt_version=os.getenv("PROMPT_VERSION", "answer_v1"),
        api_admin_key=os.getenv("API_ADMIN_KEY") or None,
        weather_url=os.getenv("WEATHER_URL", "https://api.open-meteo.com/v1/forecast"),
        weather_timeout_s=float(os.getenv("WEATHER_TIMEOUT_S", "3")),
        campus_lat=float(os.getenv("CAMPUS_LAT", "10.7626")),
        campus_lon=float(os.getenv("CAMPUS_LON", "106.6822")),
        rate_limit_per_min=int(os.getenv("RATE_LIMIT_PER_MIN", "30")),
        database_url=os.getenv("DATABASE_URL", "sqlite:///assistant.db"),
        session_salt=os.getenv("SESSION_SALT", "dev-salt"),
    )
    if s.llm_provider == "openai" and not s.llm_api_key:
        raise ConfigError(f"LLM_API_KEY is required when LLM_PROVIDER={s.llm_provider!r}")
    return s
