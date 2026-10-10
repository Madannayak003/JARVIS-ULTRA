"""Lifecycle management for JARVIS's owned Chromium CDP browser process."""

from __future__ import annotations

import socket
import subprocess
import time
import json
from pathlib import Path

import psutil
import requests

from skills.browser.browser_config import BrowserSettings
from skills.browser.browser_resolver import resolve_browser_executable
from config.settings import get_assistant_display_name


class BrowserRuntimeError(RuntimeError):
    """Raised when the dedicated JARVIS browser cannot be launched safely."""


class BrowserRuntime:
    """Launch and own one local Chromium process for a BrowserController."""

    def __init__(self, settings: BrowserSettings | None = None):
        self.settings = settings or BrowserSettings.from_environment()
        self.process: subprocess.Popen | None = None
        self.pid: int | None = None
        self.port: int | None = None
        self.executable: Path | None = None

    @property
    def endpoint(self) -> str:
        if self.port is None:
            raise BrowserRuntimeError(
                f"{get_assistant_display_name()} Browser has not selected a CDP port."
            )
        return f"http://{self.settings.cdp_host}:{self.port}"

    def resolve_profile_dir(self) -> Path:
        self.settings.profile_dir.mkdir(parents=True, exist_ok=True)
        return self.settings.profile_dir.resolve()

    @property
    def _session_file(self) -> Path:
        return self.settings.profile_dir / ".jarvis-browser-session.json"

    def _port_is_available(self, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind((self.settings.cdp_host, port))
            except OSError:
                return False
        return True

    def _select_port(self) -> int:
        if self._port_is_available(self.settings.preferred_cdp_port):
            return self.settings.preferred_cdp_port

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind((self.settings.cdp_host, 0))
            return int(probe.getsockname()[1])

    def _owned_process_is_healthy(self) -> bool:
        return (
            self._owned_process_is_running()
            and self.port is not None
            and self._cdp_is_responding()
        )

    def _owned_process_is_running(self) -> bool:
        if self.process is not None:
            return self.process.poll() is None
        return self.pid is not None and psutil.pid_exists(self.pid)

    def _write_session(self) -> None:
        self._session_file.write_text(
            json.dumps(
                {
                    "pid": self.pid,
                    "port": self.port,
                    "executable": str(self.executable),
                    "profile_dir": str(self.settings.profile_dir.resolve()),
                }
            ),
            encoding="utf-8",
        )

    def _clear_session(self) -> None:
        try:
            self._session_file.unlink()
        except FileNotFoundError:
            pass

    def _adopt_verified_session(self) -> bool:
        """Adopt a previous JARVIS process only after validating its identity."""

        try:
            session = json.loads(self._session_file.read_text(encoding="utf-8"))
            pid = int(session["pid"])
            port = int(session["port"])
            executable = Path(session["executable"]).resolve()
            profile_dir = Path(session["profile_dir"]).resolve()
            process = psutil.Process(pid)
            command_line = process.cmdline()
        except (FileNotFoundError, KeyError, TypeError, ValueError, OSError, psutil.Error):
            self._clear_session()
            return False

        expected_profile = self.settings.profile_dir.resolve()
        expected_override = self.settings.executable_override
        try:
            valid_identity = (
                profile_dir == expected_profile
                and executable.is_file()
                and Path(process.exe()).resolve() == executable
                and (
                    expected_override is None
                    or executable == expected_override.resolve()
                )
                and f"--remote-debugging-address={self.settings.cdp_host}"
                in command_line
                and f"--remote-debugging-port={port}" in command_line
                and f"--user-data-dir={expected_profile}" in command_line
            )
        except (OSError, psutil.Error):
            valid_identity = False

        if not valid_identity:
            self._clear_session()
            return False

        self.process = None
        self.pid = pid
        self.port = port
        self.executable = executable
        if self._cdp_is_responding():
            return True

        self.pid = None
        self.port = None
        self.executable = None
        self._clear_session()
        return False

    def _cdp_is_responding(self) -> bool:
        try:
            response = requests.get(f"{self.endpoint}/json/version", timeout=1)
            payload = response.json()
            return response.ok and bool(payload.get("webSocketDebuggerUrl"))
        except (requests.RequestException, ValueError):
            return False

    def ensure_running(self) -> str:
        """Return this runtime's verified CDP endpoint, launching if necessary.

        Only a subprocess started by this object is eligible for reuse. An
        arbitrary existing CDP endpoint is deliberately never adopted.
        """

        if self._owned_process_is_healthy():
            return self.endpoint

        if self._adopt_verified_session():
            return self.endpoint

        if self._owned_process_is_running():
            self.stop()

        self.executable = resolve_browser_executable(self.settings)
        profile_dir = self.resolve_profile_dir()
        self.port = self._select_port()

        arguments = [
            str(self.executable),
            f"--remote-debugging-address={self.settings.cdp_host}",
            f"--remote-debugging-port={self.port}",
            f"--user-data-dir={profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
        ]
        try:
            self.process = subprocess.Popen(
                arguments,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.pid = self.process.pid
            self._write_session()
        except OSError as error:
            self.process = None
            self.pid = None
            raise BrowserRuntimeError(
                f"{get_assistant_display_name()} Browser could not start "
                f"{self.executable}: {error}"
            ) from error

        for _ in range(30):
            if self.process.poll() is not None:
                break
            if self._cdp_is_responding():
                return self.endpoint
            time.sleep(0.25)

        exit_code = self.process.poll()
        self.stop()
        detail = "browser debugging did not become available"
        if exit_code is not None:
            detail = f"browser exited with code {exit_code}"
        raise BrowserRuntimeError(
            f"{get_assistant_display_name()} Browser could not start: {detail}."
        )

    def stop(self) -> None:
        """Stop only the browser subprocess this runtime started."""

        pid = self.pid
        self.process = None
        self.pid = None
        self.port = None
        self._clear_session()
        if pid is None or not psutil.pid_exists(pid):
            return
        try:
            owned_process = psutil.Process(pid)
            processes = owned_process.children(recursive=True) + [owned_process]
        except psutil.Error:
            return

        for owned_process in processes:
            try:
                owned_process.terminate()
            except psutil.Error:
                pass

        _gone, alive = psutil.wait_procs(processes, timeout=5)
        for owned_process in alive:
            try:
                owned_process.kill()
            except psutil.Error:
                pass

        if alive:
            psutil.wait_procs(alive, timeout=5)
