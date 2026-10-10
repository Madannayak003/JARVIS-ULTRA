"""Centralized loading and access for JARVIS environment configuration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


def load_environment(env_file: Optional[Path] = None) -> bool:
    """Load the project environment file without overriding process values."""

    return load_dotenv(
        dotenv_path=env_file or ENV_FILE,
        override=False,
    )


def get_env(name: str, default: str = "") -> str:
    """Read an environment value, treating blank optional values as missing."""

    value = os.getenv(name)
    if value is None or (value == "" and default):
        return default
    return value

