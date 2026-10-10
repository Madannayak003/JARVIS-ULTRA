"""Safe subprocess transport for Android Debug Bridge."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Sequence

from .models import AdbCommandResult, AndroidDevice


DEFAULT_ADB_PATH = Path(r"C:\platform-tools\adb.exe")
_NO_DEVICE_COMMANDS = {
    "version", "devices", "start-server", "kill-server", "connect", "disconnect",
}
_CONNECTION_MODES = {"AUTO", "USB", "LOCAL", "REMOTE"}
_REMOTE_RETRY_SECONDS = 30.0


def _adb_subprocess_options() -> dict[str, int]:
    """Return subprocess options that keep ADB console-free on Windows."""
    if os.name != "nt":
        return {}
    return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)}


def normalize_endpoint(address: str, port: int | str = 5555) -> str:
    """Validate and normalize a user-provided ADB TCP endpoint."""
    host = str(address).strip()
    if host.startswith("[") and host.endswith("]"):
        host = host[1:-1].strip()
    if not host or any(character.isspace() for character in host):
        raise ValueError("A valid Android IP address is required.")
    if not re.fullmatch(r"[A-Za-z0-9_.:-]+", host):
        raise ValueError("The Android IP address contains invalid characters.")
    try:
        normalized_port = int(port)
    except (TypeError, ValueError) as error:
        raise ValueError("The Android ADB port must be a number.") from error
    if not 1 <= normalized_port <= 65535:
        raise ValueError("The Android ADB port must be between 1 and 65535.")
    if ":" in host and not host.count(":") == 1:
        return f"[{host}]:{normalized_port}"
    return f"{host}:{normalized_port}"


class AdbError(RuntimeError):
    """Base error for an unavailable or failed ADB operation."""


class AdbNotFoundError(AdbError):
    """Raised when no usable ADB executable can be found."""


class AdbDeviceError(AdbError):
    """Raised when a device operation needs a connected device."""


class AdbCommandError(AdbError):
    """Raised when a checked ADB command returns a failure."""

    def __init__(self, result: AdbCommandResult):
        detail = result.stderr.strip() or result.stdout.strip()
        super().__init__(detail or f"ADB exited with code {result.returncode}.")
        self.result = result


class AdbClient:
    """Run ADB using safe subprocess argument lists and no shell."""

    def __init__(
        self,
        adb_path: str | os.PathLike[str] | None = None,
        device_id: str | None = None,
        timeout: float = 15.0,
        runner=subprocess.run,
    ):
        self._explicit_adb_path = str(adb_path) if adb_path else None
        self.device_id = device_id or os.getenv("ANDROID_DEVICE_ID", "").strip()
        self.timeout = timeout
        self._runner = runner
        self._selected_device_id: str | None = None
        self.connection_mode = (
            os.getenv("ANDROID_CONNECTION_MODE", "AUTO").strip().upper()
        )
        if self.connection_mode not in _CONNECTION_MODES:
            self.connection_mode = "AUTO"
        self.remote_host = os.getenv("ANDROID_REMOTE_HOST", "").strip()
        self.remote_port = os.getenv("ANDROID_REMOTE_PORT", "5555").strip() or "5555"
        self._remote_endpoint = None
        if self.remote_host:
            # * Validate configuration once, without attempting any network access.
            try:
                self._remote_endpoint = normalize_endpoint(self.remote_host, self.remote_port)
            except ValueError:
                # ! Bad optional configuration must not make JARVIS unavailable.
                self.remote_host = ""
                self.remote_port = "5555"
        self._last_remote_attempt = 0.0

    @property
    def adb_path(self) -> str | None:
        """Resolve configured ADB, PATH ADB, then the existing Windows fallback."""
        configured = self._explicit_adb_path or os.getenv("ANDROID_ADB_PATH", "").strip()
        if configured:
            return configured
        path_adb = shutil.which("adb")
        if path_adb:
            return path_adb
        if DEFAULT_ADB_PATH.exists():
            return str(DEFAULT_ADB_PATH)
        return None

    @property
    def selected_device_id(self) -> str | None:
        return self._selected_device_id or self.device_id or None

    @property
    def remote_endpoint(self) -> str | None:
        """Return the optional, explicitly configured private-network endpoint."""
        return self._remote_endpoint

    def _require_adb(self) -> str:
        path = self.adb_path
        if not path:
            raise AdbNotFoundError(
                "ADB was not found. Set ANDROID_ADB_PATH or install platform-tools."
            )
        return path

    def run_adb(
        self,
        args: Sequence[str],
        *,
        device: str | None = None,
        timeout: float | None = None,
        check: bool = False,
    ) -> AdbCommandResult:
        """Run one ADB command with each argument passed separately."""
        if not args:
            raise ValueError("ADB arguments cannot be empty.")

        normalized_args = [str(value) for value in args]
        path = self._require_adb()
        command = [path]
        if normalized_args[0] not in _NO_DEVICE_COMMANDS:
            requested_device = device or self.selected_device_id
            if requested_device:
                command.extend(["-s", requested_device])
            else:
                selected = self.select_device()
                if not selected:
                    raise AdbDeviceError("No online Android device is connected.")
                command.extend(["-s", selected.serial])
        command.extend(normalized_args)

        try:
            completed = self._runner(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout or self.timeout,
                check=False,
                shell=False,
                **_adb_subprocess_options(),
            )
        except FileNotFoundError as error:
            raise AdbNotFoundError(f"ADB executable is not available: {path}") from error
        except subprocess.TimeoutExpired as error:
            raise AdbError("ADB command timed out.") from error
        except OSError as error:
            raise AdbError(f"ADB could not be started: {error}") from error

        result = AdbCommandResult(
            command=tuple(command),
            returncode=int(completed.returncode),
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
        )
        if check and not result.ok:
            raise AdbCommandError(result)
        return result

    def is_available(self) -> bool:
        try:
            return self.run_adb(["version"]).ok
        except AdbError:
            return False

    def detect_adb(self) -> bool:
        """Compatibility-friendly name for the ADB availability check."""
        return self.is_available()

    def get_devices(self) -> list[AndroidDevice]:
        result = self.run_adb(["devices", "-l"])
        if not result.ok:
            return []

        devices: list[AndroidDevice] = []
        for raw_line in result.stdout.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("List of devices"):
                continue
            fields = line.split()
            if len(fields) < 2:
                continue
            attributes: dict[str, str] = {}
            for field in fields[2:]:
                if ":" in field:
                    key, value = field.split(":", 1)
                    attributes[key] = value
            devices.append(
                AndroidDevice(
                    serial=fields[0],
                    state=fields[1],
                    product=attributes.get("product", ""),
                    model=attributes.get("model", "").replace("_", " "),
                    device=attributes.get("device", ""),
                    transport_id=attributes.get("transport_id", ""),
                )
            )
        return devices

    def connect(self, address: str, port: int | str = 5555) -> AdbCommandResult:
        """Connect one explicitly requested wireless ADB endpoint."""
        endpoint = normalize_endpoint(address, port)
        return self.run_adb(["connect", endpoint])

    def connect_remote(self) -> AdbCommandResult | None:
        """Try the configured private-network endpoint once per retry window.

        This is deliberately opt-in through ANDROID_REMOTE_HOST and never scans
        or discovers arbitrary network addresses.
        """
        if self.connection_mode in {"USB", "LOCAL"} or not self._remote_endpoint:
            return None
        now = time.monotonic()
        if now - self._last_remote_attempt < _REMOTE_RETRY_SECONDS:
            return None
        self._last_remote_attempt = now
        host, port = self._remote_endpoint.rsplit(":", 1)
        host = host.strip("[]")
        try:
            return self.connect(host, port)
        except AdbError:
            return None

    def disconnect(self, endpoint: str) -> AdbCommandResult:
        """Disconnect only one explicitly requested wireless endpoint."""
        value = str(endpoint).strip()
        if not value or ":" not in value:
            raise ValueError("A wireless Android endpoint is required.")
        address, port = value.rsplit(":", 1)
        return self.run_adb(["disconnect", normalize_endpoint(address, port)])

    def select_device(self, device_id: str | None = None) -> AndroidDevice | None:
        devices = self.get_devices()
        requested = device_id or self.device_id
        if requested:
            selected = next(
                (item for item in devices if item.serial == requested and item.is_online),
                None,
            )
        else:
            online = [item for item in devices if item.is_online]
            if self.connection_mode == "USB":
                selected = next((item for item in online if not item.is_wireless), None)
            elif self.connection_mode == "LOCAL":
                selected = next((item for item in online if item.is_wireless), None)
            elif self.connection_mode == "REMOTE":
                selected = next(
                    (item for item in online if item.serial == self._remote_endpoint),
                    None,
                )
            else:
                selected = next((item for item in online if not item.is_wireless), None)
                if selected is None:
                    selected = next(iter(online), None)

        if (
            selected is None
            and not requested
            and self.connection_mode in {"AUTO", "REMOTE"}
            and self._remote_endpoint
        ):
            self.connect_remote()
            devices = self.get_devices()
            selected = next(
                (item for item in devices if item.is_online and item.serial == self._remote_endpoint),
                None,
            )
        self._selected_device_id = selected.serial if selected else None
        return selected

    def connection_type(self, device: AndroidDevice) -> str:
        """Normalize the selected transport without changing device identity."""
        if not device.is_wireless:
            return "USB"
        if self._remote_endpoint and device.serial == self._remote_endpoint:
            return "REMOTE"
        return "Wireless"

    @staticmethod
    def endpoint_parts(endpoint: str | None) -> tuple[str, int | None]:
        """Split an ADB endpoint for safe status/API presentation."""
        if not endpoint or ":" not in endpoint:
            return "", None
        host, port = endpoint.rsplit(":", 1)
        try:
            return host.strip("[]"), int(port)
        except ValueError:
            return host.strip("[]"), None

    def shell(
        self,
        args: Sequence[str],
        *,
        device: str | None = None,
        check: bool = False,
    ) -> AdbCommandResult:
        """Run ``adb shell`` with safe individual arguments."""
        return self.run_adb(
            ["shell", *[str(value) for value in args]],
            device=device,
            check=check,
        )
