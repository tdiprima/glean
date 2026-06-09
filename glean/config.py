"""Configuration. Secrets come from the environment only — never hardcoded.

Validated at startup; missing required values fail fast.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class Config:
    openai_api_key: str
    model: str
    github_token: str | None
    db_path: str
    max_steps: int


def _require_positive_int(name: str, raw: str, default: int) -> int:
    """Parse an int env var, falling back to a default, rejecting bad values."""
    if raw == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from exc
    if value <= 0:
        raise ConfigError(f"{name} must be positive, got {value}")
    return value


def load_config() -> Config:
    """Build a validated Config from the environment. Fails fast if unusable."""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ConfigError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    return Config(
        openai_api_key=api_key,
        model=os.environ.get("OPENAI_MODEL", "gpt-5.2").strip() or "gpt-5.2",
        github_token=(os.environ.get("GITHUB_TOKEN", "").strip() or None),
        db_path=os.environ.get("GLEAN_DB", "glean.db").strip() or "glean.db",
        max_steps=_require_positive_int(
            "GLEAN_MAX_STEPS", os.environ.get("GLEAN_MAX_STEPS", ""), 12
        ),
    )
