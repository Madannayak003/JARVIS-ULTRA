"""Configuration for JARVIS's dedicated Chromium browser instance."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_CDP_HOST = "127.0.0.1"
DEFAULT_CDP_PORT = 9223


class BrowserConfigurationError(ValueError):
    """Raised when a JARVIS browser environment setting is invalid."""


def _local_app_data() -> Path:
    """Return a per-user local data directory without embedding a username."""

    return Path(
        os.environ.get(
            "LOCALAPPDATA",
            Path.home() / "AppData" / "Local",
        )
    )


def _configured_path(name: str, default: Path | None = None) -> Path | None:
    value = os.environ.get(name)
    if value:
        return Path(os.path.expandvars(value)).expanduser()
    return default


@dataclass(frozen=True)
class BrowserSettings:
    """Settings shared by executable discovery and the CDP runtime."""

    executable_override: Path | None
    profile_dir: Path
    cdp_host: str
    preferred_cdp_port: int

    @classmethod
    def from_environment(cls) -> "BrowserSettings":
        host = (
            os.environ.get("JARVIS_BROWSER_CDP_HOST")
            or DEFAULT_CDP_HOST
        ).strip()
        if host != DEFAULT_CDP_HOST:
            raise BrowserConfigurationError(
                "JARVIS_BROWSER_CDP_HOST must be 127.0.0.1 so the browser "
                "debugging endpoint remains local-only."
            )

        raw_port = (
            os.environ.get("JARVIS_BROWSER_CDP_PORT")
            or str(DEFAULT_CDP_PORT)
        )
        try:
            port = int(raw_port)
        except ValueError as error:
            raise BrowserConfigurationError(
                "JARVIS_BROWSER_CDP_PORT must be an integer from 1 to 65535."
            ) from error

        if not 1 <= port <= 65535:
            raise BrowserConfigurationError(
                "JARVIS_BROWSER_CDP_PORT must be an integer from 1 to 65535."
            )

        return cls(
            executable_override=_configured_path("JARVIS_BROWSER_EXECUTABLE"),
            profile_dir=_configured_path(
                "JARVIS_BROWSER_PROFILE_DIR",
                _local_app_data() / "JARVIS" / "ChromeProfile",
            ),
            cdp_host=host,
            preferred_cdp_port=port,
        )
