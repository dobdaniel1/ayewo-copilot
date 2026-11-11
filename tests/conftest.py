from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


@pytest.fixture
def spec_path():
    return EXAMPLES / "switch_requirements.md"


@pytest.fixture
def log_path():
    def _get(name: str) -> Path:
        return EXAMPLES / "logs" / f"{name}.log"

    return _get
