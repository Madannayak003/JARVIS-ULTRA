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
    manager = get_android_manager()
    status = manager.device_status()
    if not status.selected_device:
        _say("No online Android device is connected.")
        return False
    details = status.selected_device.display_name
    if status.model and status.model.casefold() not in details.casefold():
        details = f"{details}, {status.model}"
    if status.android_version:
        details = f"{details}, Android {status.android_version}"
    connection = manager.adb.connection_type(status.selected_device)
    details = f"{details}, connected over {connection}"
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


def android_close_app(data=None):
    data = data or {}
    app = str(data.get("app", "")).strip()
    package = str(data.get("package", "")).strip() or None
    if not app and not package:
        _say("Please tell me which Android app to close.")
        return False
    result = get_android_manager().close_app(app or package or "", package=package)
    if result.success:
        _say(f"Closed {result.package or app} on Android.")
        return True
    _say(result.detail or f"I could not close {app or package} on Android.")
    return False


def android_list_apps(data=None):
    apps = get_android_manager().query_installed_applications()
    if not apps:
        _say("I could not read installed applications from the Android device.")
        return False
    _say(f"The phone has {len(apps)} installed applications.")
    return {"ok": True, "applications": apps, "count": len(apps)}


def android_search_apps(data=None):
    query = str((data or {}).get("query", "")).strip().casefold()
    if not query:
        _say("Please tell me what application to search for.")
        return False
    apps = [item for item in get_android_manager().query_installed_applications() if query in item.casefold()]
    _say(f"I found {len(apps)} matching applications.")
    return {"ok": True, "applications": apps, "count": len(apps)}


def android_battery_status(data=None):
    battery = get_android_manager().battery_status()
    if battery is None:
        _say("I could not read the phone battery status.")
        return False
    parts = []
    if battery.percentage is not None:
        parts.append(f"{battery.percentage:g} percent")
    if battery.status:
        state = battery.status.casefold()
        parts.append("charging" if state in {"charging", "full"} else "discharging" if state == "discharging" else battery.status)
    if not parts:
        _say("The phone returned no usable battery values.")
        return False
    _say("Your phone battery is at " + " and is ".join(parts) + ".")
    return {"ok": True, "percentage": battery.percentage, "status": battery.status, "plugged": battery.plugged, "health": battery.health, "temperature_c": battery.temperature_c, "voltage_v": battery.voltage_v}


def android_foreground_app(data=None):
    package = get_android_manager().foreground_package()
    if not package:
        _say("The foreground Android app is not available from this device.")
        return False
    _say(f"The foreground Android app is {package}.")
    return {"ok": True, "package": package}


def android_home(data=None):
    result = get_android_manager().go_home()
    if result.success:
        _say("Returned the phone to its home screen.")
        return True
    _say(result.detail)
    return False


def android_search_youtube(data=None):
    query = str((data or {}).get("query", "")).strip()
    if not query:
        _say("Please tell me what to search for on YouTube.")
        return False
    result = get_android_manager().search_youtube(query)
    if result.success:
        _say(f"Searching YouTube for {query}.")
        return True
    _say(result.detail)
    return False


def android_search_web(data=None):
    values = data or {}
    query = str(values.get("query", "")).strip()
    provider = str(values.get("provider", "google")).strip() or "google"
    if not query:
        _say("Please tell me what to search for.")
        return False
    try:
        result = get_android_manager().search_web(query, provider)
    except ValueError as error:
        _say(str(error))
        return False
    if result.success:
        _say(f"Searching {provider} for {query}.")
        return True
    _say(result.detail)
    return False


def android_camera(data=None):
    facing = str((data or {}).get("facing", "")).strip().casefold() or None
    result = get_android_manager().open_camera(facing)
    if result.success:
        if facing:
            _say(f"Opened the {facing} camera. The camera app controls whether lens selection is honored.")
        else:
            _say("Opened the camera.")
        return True
    _say(result.detail)
    return False


def android_capture_photo(data=None):
    facing = str((data or {}).get("facing", "rear")).strip().casefold()
    result = get_android_manager().capture_photo(facing)
    if result.success:
        _say(f"Photo captured and saved{f' at {result.location}' if result.location else ''}.")
        return {"ok": True, "location": result.location, "package": result.package}
    _say(result.detail)
    return False


def android_flashlight(data=None):
    enabled = str((data or {}).get("state", "")).strip().casefold() == "on"
    result = get_android_manager().flashlight(enabled)
    if result.success:
        _say(f"Flashlight turned {'on' if enabled else 'off'}.")
        return True
    _say(result.detail)
    return False


def android_flashlight_on(data=None):
    return android_flashlight({"state": "on"})


def android_flashlight_off(data=None):
    return android_flashlight({"state": "off"})


def android_open_front_camera(data=None):
    return android_camera({"facing": "front"})


def android_open_rear_camera(data=None):
    return android_camera({"facing": "rear"})


register("android_check_adb", android_check_adb, category="android_control")
register("android_check_device", android_check_device, category="android_control")
register("android_device_info", android_device_info, category="android_control")
register("android_open_app", android_open_app, category="android_control")
register("android_launch_app", android_launch_app, category="android_control")
register("android_close_app", android_close_app, category="android_control")
register("android_list_apps", android_list_apps, category="android_control")
register("android_search_apps", android_search_apps, category="android_control")
register("android_battery_status", android_battery_status, category="android_control")
register("android_foreground_app", android_foreground_app, category="android_control")
register("android_home", android_home, category="android_control")
register("android_search_youtube", android_search_youtube, category="android_control")
register("android_search_web", android_search_web, category="android_control")
register("android_camera", android_camera, category="android_control")
register("android_capture_photo", android_capture_photo, category="android_control")
register("android_flashlight", android_flashlight, category="android_control")
register("android_flashlight_on", android_flashlight_on, category="android_control")
register("android_flashlight_off", android_flashlight_off, category="android_control")
register("android_open_front_camera", android_open_front_camera, category="android_control")
register("android_open_rear_camera", android_open_rear_camera, category="android_control")
