"""Small data models shared by the Android bridge and its skills."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdbCommandResult:
    """Captured result from one safe, argument-list ADB invocation."""

    command: tuple[str, ...]
    returncode: int
    stdout: str = ""
    stderr: str = ""

    @property
    def ok(self) -> bool:
        return self.returncode == 0


@dataclass(frozen=True)
class AndroidDevice:
    """One row returned by ``adb devices -l``."""

    serial: str
    state: str
    product: str = ""
    model: str = ""
    device: str = ""
    transport_id: str = ""

    @property
    def is_online(self) -> bool:
        return self.state == "device"

    @property
    def is_wireless(self) -> bool:
        """ADB serials for TCP/IP devices are represented as host:port."""
        return ":" in self.serial

    @property
    def connection_type(self) -> str:
        return "Wireless" if self.is_wireless else "USB"

    @property
    def endpoint(self) -> str | None:
        return self.serial if self.is_wireless else None

    @property
    def display_name(self) -> str:
        return self.model or self.product or self.serial


@dataclass(frozen=True)
class DeviceStatus:
    """Safe, non-sensitive snapshot of ADB and connected-device state."""

    adb_available: bool
    adb_path: str | None
    devices: tuple[AndroidDevice, ...] = ()
    selected_device: AndroidDevice | None = None
    model: str = ""
    android_version: str = ""


@dataclass(frozen=True)
class AndroidConnectionStatus:
    """Compact connection snapshot for local UI/API consumers."""

    adb_available: bool
    adb_path: str | None
    connected: bool = False
    selected_device: AndroidDevice | None = None
    model: str = ""
    android_version: str = ""
    connection_type: str = ""
    endpoint: str | None = None
    wireless_endpoints: tuple[str, ...] = ()
    host: str = ""
    port: int | None = None
    error: str = ""


@dataclass(frozen=True)
class IntentSpec:
    """An Android intent represented without shell syntax."""

    action: str
    categories: tuple[str, ...] = ()
    data: str | None = None
    mime_type: str | None = None
    package: str | None = None
    component: str | None = None


@dataclass(frozen=True)
class AppLaunchResult:
    """Outcome of resolving and launching an Android application."""

    success: bool
    app_name: str
    package: str | None = None
    error_code: str | None = None
    detail: str = ""
