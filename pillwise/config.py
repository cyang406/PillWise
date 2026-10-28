"""Runtime settings, read once from the environment / .env.

FROZEN FILE (shared contract). Add a new setting only via a contract-change
commit on `main`. Every branch reads settings from here; never call os.getenv
elsewhere.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:  # python-dotenv is optional at import time so tests never need a .env
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"


def _flag(name: str, default: str) -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    # When True, pillwise.api returns canned results from pillwise.mocks.
    # Default ON so the UI works before the pipeline exists.
    mock: bool = field(default_factory=lambda: _flag("PILLWISE_MOCK", "1"))
    # When True, network calls (RxNorm, openFDA) read/write data/cache/ only.
    offline: bool = field(default_factory=lambda: _flag("PILLWISE_OFFLINE", "0"))

    anthropic_api_key: str | None = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    openfda_api_key: str | None = field(default_factory=lambda: os.getenv("OPENFDA_API_KEY"))

    # Models: reasoning/vision vs. cheap text steps.
    model_main: str = field(default_factory=lambda: os.getenv("PILLWISE_MODEL_MAIN", "claude-sonnet-5-5"))
    model_fast: str = field(default_factory=lambda: os.getenv("PILLWISE_MODEL_FAST", "claude-haiku-5-5"))

    ddinter_db: Path = field(
        default_factory=lambda: Path(os.getenv("PILLWISE_DDINTER_DB", DATA_DIR / "ddinter.sqlite"))
    )
    audit_db: Path = field(default_factory=lambda: Path(os.getenv("PILLWISE_AUDIT_DB", DATA_DIR / "audit.sqlite")))
    cache_dir: Path = field(default_factory=lambda: Path(os.getenv("PILLWISE_CACHE_DIR", DATA_DIR / "cache")))
    beers_path: Path = DATA_DIR / "beers.json"
    onc_path: Path = DATA_DIR / "onc_high.json"
    scenarios_dir: Path = DATA_DIR / "scenarios"

    # Plain-language target (stretch A).
    target_reading_grade: float = 6.0
    drift_threshold: float = 0.80


def get_settings() -> Settings:
    """Re-read the environment each call so tests can monkeypatch env vars."""
    return Settings()
