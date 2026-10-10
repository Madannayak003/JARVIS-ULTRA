"""
=============================================================
JARVIS PRO — WINDOWS INTEGRATION
=============================================================

Windows-only helpers used by the JARVIS PRO local HUD.

Provides:

    - Create JARVIS desktop shortcut
    - Read Windows auto-start status
    - Enable / disable JARVIS auto-start

This module does not start JARVIS immediately.
It only creates/manages the Windows integration entries.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


# * =============================================================
# * JARVIS PATHS
# * =============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

MAIN_PY = (
    PROJECT_ROOT
    / "run_jarvis.py"
)

ICON_PATH = PROJECT_ROOT / "assets" / "icons" / "jarvis.ico"

SHORTCUT_NAME = "JARVIS PRO.lnk"


# * =============================================================
# * WINDOWS CHECK
# * =============================================================

def _require_windows() -> None:

    if os.name != "nt":

        raise RuntimeError(
            "Windows integration is only available on Windows."
        )


# * =============================================================
# * PYTHON EXECUTABLE
# * =============================================================

def _python_executable() -> str:
    """
    Return pythonw.exe when available so the Windows
    desktop shortcut launches JARVIS without a console window.

    Falls back to the current Python executable if
    pythonw.exe is unavailable.
    """

    current_python = (
        Path(sys.executable)
        .resolve()
    )

    pythonw = (
        current_python
        .with_name("pythonw.exe")
    )

    if pythonw.is_file():

        return str(
            pythonw
        )

    return str(
        current_python
    )


# * =============================================================
# * DESKTOP PATH
# * =============================================================

def _desktop_directory() -> Path:
    if os.name == "nt":
        try:
            import winreg

            key_path = (
                r"Software\Microsoft\Windows\CurrentVersion"
                r"\Explorer\Shell Folders"
            )

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                desktop = Path(winreg.QueryValueEx(key, "Desktop")[0])

            desktop.mkdir(parents=True, exist_ok=True)
            return desktop

        except Exception:
            pass

    desktop = Path.home() / "Desktop"
    desktop.mkdir(parents=True, exist_ok=True)
    return desktop


# * =============================================================
# * DESKTOP SHORTCUT
# * =============================================================

def create_desktop_shortcut() -> str:
    """
    Create or replace the JARVIS PRO desktop shortcut.

    The shortcut launches:

        python run_jarvis.py

    from the actual JARVIS PRO project directory.
    """

    _require_windows()

    if not MAIN_PY.is_file():

        raise FileNotFoundError(
            f"JARVIS PRO launcher was not found: {MAIN_PY}"
        )

    desktop = (
        _desktop_directory()
    )

    shortcut_path = (
        desktop
        / SHORTCUT_NAME
    )

    python_exe = (
        _python_executable()
    )

    # * ---------------------------------------------------------
    # * PowerShell creates a native Windows .lnk file.
    #
    # ! No pywin32 dependency is required.
    # * ---------------------------------------------------------

    ps_script = r"""
$ErrorActionPreference = "Stop"

$WshShell = New-Object -ComObject WScript.Shell

$Shortcut = $WshShell.CreateShortcut($env:JARVIS_SHORTCUT_PATH)

$Shortcut.TargetPath = $env:JARVIS_PYTHON

$Shortcut.Arguments = $env:JARVIS_MAIN

$Shortcut.WorkingDirectory = $env:JARVIS_ROOT

$Shortcut.Description = "JARVIS PRO"

$Shortcut.WindowStyle = 7

if ($env:JARVIS_ICON) {
    $Shortcut.IconLocation = "$env:JARVIS_ICON,0"
} else {
    $Shortcut.IconLocation = "$env:JARVIS_PYTHON,0"
}

$Shortcut.Save()
"""

    environment = os.environ.copy()

    environment[
        "JARVIS_SHORTCUT_PATH"
    ] = str(shortcut_path)

    environment[
        "JARVIS_PYTHON"
    ] = python_exe

    environment[
        "JARVIS_MAIN"
    ] = f'"{MAIN_PY}"'

    environment[
        "JARVIS_ROOT"
    ] = str(PROJECT_ROOT)
    
    environment[
        "JARVIS_ICON"
    ] = str(ICON_PATH) if ICON_PATH.is_file() else ""

    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            ps_script,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
        check=False,
    )

    if result.returncode != 0:

        error = (
            result.stderr.strip()
            or result.stdout.strip()
            or "Unknown PowerShell error."
        )

        raise RuntimeError(
            f"Could not create desktop shortcut: {error}"
        )

    if not shortcut_path.is_file():

        raise RuntimeError(
            "Windows reported success, but the shortcut "
            "was not created."
        )

    print(
        "[WINDOWS] Desktop shortcut created:"
    )

    print(
        f"[WINDOWS] {shortcut_path}"
    )

    return (
        f"Desktop shortcut created: "
        f"{shortcut_path.name}"
    )


# * =============================================================
# * WINDOWS STARTUP DIRECTORY
# * =============================================================

def _startup_directory() -> Path:
    """
    Return the user's Windows Startup directory.
    """

    appdata = os.environ.get(
        "APPDATA"
    )

    if not appdata:

        raise RuntimeError(
            "APPDATA environment variable is unavailable."
        )

    startup = (
        Path(appdata)
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs"
        / "Startup"
    )

    startup.mkdir(
        parents=True,
        exist_ok=True,
    )

    return startup


# * =============================================================
# * AUTO-START SHORTCUT
# * =============================================================

def _autostart_shortcut_path() -> Path:

    return (
        _startup_directory()
        / SHORTCUT_NAME
    )


# * =============================================================
# * AUTO-START STATUS
# * =============================================================

def get_autostart_status() -> bool:
    """
    Return True when JARVIS PRO is configured to start
    automatically when the current Windows user logs in.
    """

    _require_windows()

    return _autostart_shortcut_path().is_file()


# * =============================================================
# * ENABLE / DISABLE AUTO-START
# * =============================================================

def set_autostart(
    enabled: bool,
) -> str:
    """
    Enable or disable JARVIS PRO Windows auto-start.

    Enable:
        Creates a JARVIS PRO shortcut in the user's
        Windows Startup folder.

    Disable:
        Removes that shortcut.
    """

    _require_windows()

    shortcut_path = (
        _autostart_shortcut_path()
    )

    if not enabled:

        if shortcut_path.exists():

            shortcut_path.unlink()

            print("[WINDOWS] JARVIS PRO auto-start disabled.")

        else:

            print("[WINDOWS] JARVIS PRO auto-start was already disabled.")

        return "JARVIS PRO auto-start disabled."

    # * ---------------------------------------------------------
    # * Enable
    # * ---------------------------------------------------------

    if not MAIN_PY.is_file():

        raise FileNotFoundError(
            f"JARVIS PRO launcher was not found: {MAIN_PY}"
        )

    python_exe = (
        _python_executable()
    )

    ps_script = r"""
$ErrorActionPreference = "Stop"

$WshShell = New-Object -ComObject WScript.Shell

$Shortcut = $WshShell.CreateShortcut($env:JARVIS_STARTUP_PATH)

$Shortcut.TargetPath = $env:JARVIS_PYTHON

$Shortcut.Arguments = $env:JARVIS_MAIN

$Shortcut.WorkingDirectory = $env:JARVIS_ROOT

$Shortcut.Description = "JARVIS PRO Auto Start"

if ($env:JARVIS_ICON) {
    $Shortcut.IconLocation = "$env:JARVIS_ICON,0"
} else {
    $Shortcut.IconLocation = "$env:JARVIS_PYTHON,0"
}

$Shortcut.Save()
"""

    environment = os.environ.copy()

    environment[
        "JARVIS_STARTUP_PATH"
    ] = str(shortcut_path)

    environment[
        "JARVIS_PYTHON"
    ] = python_exe

    environment[
        "JARVIS_MAIN"
    ] = f'"{MAIN_PY}"'

    environment[
        "JARVIS_ROOT"
    ] = str(PROJECT_ROOT)
    
    environment[
        "JARVIS_ICON"
    ] = str(ICON_PATH) if ICON_PATH.is_file() else ""

    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            ps_script,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
        check=False,
    )

    if result.returncode != 0:

        error = (
            result.stderr.strip()
            or result.stdout.strip()
            or "Unknown PowerShell error."
        )

        raise RuntimeError(
            f"Could not configure auto-start: {error}"
        )

    if not shortcut_path.is_file():

        raise RuntimeError(
            "Windows reported success, but the auto-start "
            "shortcut was not created."
        )

    print("[WINDOWS] JARVIS PRO auto-start enabled.")

    return "JARVIS PRO auto-start enabled."
