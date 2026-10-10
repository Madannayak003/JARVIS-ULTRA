"""Safe, simple Android Control actions backed by the shared ADB bridge."""

from __future__ import annotations

from core.registry import register
from services.android import get_android_manager


def _say(message: str) -> None:
    print(f"[ANDROID] {message}")
    try:
        from voice.manager import speak
        speak(message)
    except Exception:
        # * Keep headless/test environments usable without the optional voice stack.
        pass


def android_check_adb(data=None):
    manager = get_android_manager()
    if manager.adb.is_available():
        _say(f"ADB is available at {manager.adb.adb_path}.")
        return True
    _say("ADB is not available. Set ANDROID_ADB_PATH or install platform-tools.")
    return False


def android_check_device(data=None):
    status = get_android_manager().device_status()
    if not status.adb_available:
        _say("ADB is not available, so I cannot check the Android phone.")
        return False
    if not status.devices:
        _say("No Android device is connected.")
        return False
    if not status.selected_device:
        _say("An Android device was found, but it is not authorized or online.")
        return False
    _say(f"Android device connected: {status.selected_device.display_name}.")
    return True


def android_device_info(data=None):
    status = get_android_manager().device_status()
    if not status.selected_device:
        _say("No online Android device is connected.")
        return False
    details = status.selected_device.display_name
    if status.model and status.model.casefold() not in details.casefold():
        details = f"{details}, {status.model}"
    if status.android_version:
        details = f"{details}, Android {status.android_version}"
    _say(f"Connected Android device: {details}.")
    return True


def android_open_app(data=None):
    data = data or {}
    app_name = str(data.get("app", "")).strip()
    if not app_name:
        _say("Please tell me which Android app to open.")
        return False

    result = get_android_manager().open_app(app_name)
    if result.success:
        _say(f"Opened {app_name} on Android.")
        return True
    if result.error_code == "not_installed":
        _say(f"{app_name} is not available on the connected Android device.")
    elif result.error_code == "bridge_unavailable":
        _say(f"I could not open {app_name}: {result.detail}")
    else:
        _say(f"I could not open {app_name} on Android.")
    return False


def android_launch_app(data=None):
    return android_open_app(data)


register("android_check_adb", android_check_adb, category="android_control")
register("android_check_device", android_check_device, category="android_control")
register("android_device_info", android_device_info, category="android_control")
register("android_open_app", android_open_app, category="android_control")
register("android_launch_app", android_launch_app, category="android_control")
