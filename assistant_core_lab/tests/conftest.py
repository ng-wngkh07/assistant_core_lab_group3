from pathlib import Path

import pytest

from assistant_core.config import Settings
from assistant_core.knowledge import Handbook, OfficeDirectory
from assistant_core.responder import StubLLMResponder
from assistant_core.service import AssistantService


@pytest.fixture
def data_dir() -> Path:
    return Path(__file__).parent.parent / "data"


@pytest.fixture
def settings(data_dir: Path) -> Settings:
    return Settings(
        data_dir=data_dir,
        llm_provider="stub",
        credit_rate_vnd=450_000,
        retake_multiplier=1.5,
        max_credits=30,
        log_level="INFO",
        database_url="sqlite://",
    )


@pytest.fixture
def offices(data_dir: Path) -> OfficeDirectory:
    return OfficeDirectory.from_csv(data_dir / "offices.csv")


@pytest.fixture
def handbook(data_dir: Path) -> Handbook:
    return Handbook.from_json(data_dir / "handbook.json")


@pytest.fixture
def responder() -> StubLLMResponder:
    return StubLLMResponder()


@pytest.fixture
def service(
    settings: Settings,
    offices: OfficeDirectory,
    handbook: Handbook,
    responder: StubLLMResponder,
) -> AssistantService:
    return AssistantService(settings, offices, handbook, responder)
