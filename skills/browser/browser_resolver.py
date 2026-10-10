"""Windows Chromium executable discovery for the JARVIS browser runtime."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from skills.browser.browser_config import BrowserSettings
from config.settings import get_assistant_display_name


class BrowserExecutableNotFoundError(RuntimeError):
    """Raised when no supported local Chromium browser is available."""


def _windows_roots() -> list[Path]:
    """Return unique, existing-or-potential Windows installation roots."""

    roots: list[Path] = []
    for name in ("LOCALAPPDATA", "PROGRAMFILES", "PROGRAMFILES(X86)"):
        value = os.environ.get(name)
        if value:
            root = Path(value)
            if root not in roots:
                roots.append(root)
    return roots


def _candidates(relative_paths: tuple[str, ...]) -> list[Path]:
    return [root / relative for root in _windows_roots() for relative in relative_paths]


def _first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.is_file():
            return path.resolve()
    return None


def resolve_browser_executable(settings: BrowserSettings) -> Path:
    """Resolve an explicitly configured browser, Chrome, Edge, or Chromium."""

    if settings.executable_override is not None:
        executable = settings.executable_override
        if executable.is_file():
            return executable.resolve()
        raise BrowserExecutableNotFoundError(
            "JARVIS_BROWSER_EXECUTABLE does not point to an executable file: "
            f"{executable}"
        )

    browser_families = (
        ("Google Chrome", ("Google/Chrome/Application/chrome.exe",)),
        ("Microsoft Edge", ("Microsoft/Edge/Application/msedge.exe",)),
        (
            "Chromium",
            (
                "Chromium/Application/chrome.exe",
                "Chromium/Application/chromium.exe",
            ),
        ),
    )
    for _name, relative_paths in browser_families:
        found = _first_existing(_candidates(relative_paths))
        if found is not None:
            return found

    # * This additionally supports a supported browser explicitly available on PATH.
    for command in ("chrome.exe", "msedge.exe", "chromium.exe"):
        found = shutil.which(command)
        if found:
            return Path(found).resolve()

    raise BrowserExecutableNotFoundError(
        f"{get_assistant_display_name()} Browser could not find a supported "
        "Chrome/Chromium browser. "
        "Install Google Chrome, Microsoft Edge, or Chromium, or configure "
        "JARVIS_BROWSER_EXECUTABLE."
    )
