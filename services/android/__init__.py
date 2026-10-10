"""Reusable Android/ADB transport primitives.

This package intentionally contains no voice-command interpretation and no
payment behavior. Skills use :class:`AndroidDeviceManager` for device and
application operations.
"""

from .adb_client import (
    AdbClient,
    AdbCommandError,
    AdbDeviceError,
    AdbError,
    AdbNotFoundError,
    normalize_endpoint,
)
from .device_manager import AndroidDeviceManager
from .models import (
    AdbCommandResult,
    AndroidConnectionStatus,
    AndroidDevice,
    AppLaunchResult,
    DeviceStatus,
    IntentSpec,
)

_manager = None


def get_android_manager() -> AndroidDeviceManager:
    """Return the process-wide Android bridge used by the skills."""
    global _manager
    if _manager is None:
        _manager = AndroidDeviceManager()
    return _manager


__all__ = [
    "AdbClient", "AdbCommandError", "AdbDeviceError", "AdbError",
    "AdbNotFoundError", "AdbCommandResult", "normalize_endpoint",
    "AndroidConnectionStatus", "AndroidDevice", "AndroidDeviceManager", "AppLaunchResult", "DeviceStatus",
    "IntentSpec", "get_android_manager",
]
