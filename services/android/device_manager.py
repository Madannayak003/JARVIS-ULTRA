"""Higher-level, still generic Android device and app primitives."""

from __future__ import annotations

import re
import json
import os
import time
import uuid
from typing import Sequence
from urllib.parse import urlparse

from .adb_client import AdbClient, AdbError, normalize_endpoint
from .android_intents import (
    ACTION_MAIN,
    CATEGORY_LAUNCHER,
    normalize_app_name,
    package_hints_for,
    standard_intent_for,
    CATEGORY_HOME,
    ACTION_HOME,
    youtube_search_url,
    web_search_url,
)
from .models import (
    AndroidConnectionStatus, AndroidOperationResult, AppLaunchResult,
    BatteryStatus, DeviceStatus, IntentSpec,
)


class AndroidDeviceManager:
    """Reusable bridge operations shared by independent skills."""

    def __init__(self, adb_client: AdbClient | None = None):
        self.adb = adb_client or AdbClient()
        self.companion_package = os.getenv("ANDROID_COMPANION_PACKAGE", "com.jarvis.androidcontrol").strip()

    def get_devices(self):
        return self.adb.get_devices()

    def detect_devices(self):
        """Return the currently visible ADB devices."""
        return self.get_devices()

    def get_selected_device(self):
        selected_id = self.adb.selected_device_id
        if selected_id:
            selected = self.adb.select_device(selected_id)
            if selected is not None:
                return selected
        return self.adb.select_device()

    def select_device(self, device_id: str | None = None):
        return self.adb.select_device(device_id)

    def run_adb(self, args: Sequence[str], **kwargs):
        return self.adb.run_adb(args, **kwargs)

    def connect_wireless(self, address: str, port: int | str = 5555):
        """Connect one user-selected wireless endpoint through the shared bridge."""
        endpoint = normalize_endpoint(address, port)
        result = self.adb.connect(address, port)
        if result.ok:
            # * Make the explicitly requested endpoint the active bridge target
            # * when it is visible, while retaining USB fallback after disconnect.
            self.adb.pin_device(endpoint)
        return result

    def disconnect_wireless(self, endpoint: str):
        """Disconnect only the requested wireless endpoint."""
        return self.adb.disconnect(endpoint)

    def launch_intent(self, intent: IntentSpec, *, device: str | None = None) -> bool:
        """Launch an intent without coordinates, taps, or text injection."""
        args = ["shell", "am", "start", "-W"]
        if intent.component:
            args.extend(["-n", intent.component])
        else:
            args.extend(["-a", intent.action])
        args.extend([item for category in intent.categories for item in ("-c", category)])
        if intent.data:
            args.extend(["-d", intent.data])
        if intent.mime_type:
            args.extend(["-t", intent.mime_type])
        if intent.package and not intent.component:
            args.extend(["-p", intent.package])
        for extra_type, key, value in intent.extras:
            if extra_type not in {"ez", "ei", "es"}:
                raise ValueError("Unsupported Android intent extra type.")
            args.extend([f"--{extra_type}", key, value])

        result = self.adb.run_adb(args, device=device)
        output = f"{result.stdout}\n{result.stderr}".casefold()
        failure_markers = (
            "error:",
            "no activity found",
            "unable to resolve intent",
            "exception occurred while executing",
        )
        return result.ok and not any(marker in output for marker in failure_markers)

    def installed_packages(self) -> list[str]:
        result = self.adb.shell(["pm", "list", "packages"])
        if not result.ok:
            return []
        packages = []
        for line in result.stdout.splitlines():
            value = line.strip()
            if value.startswith("package:"):
                package = value.removeprefix("package:").strip()
                if package:
                    packages.append(package)
        return packages

    def query_installed_applications(self) -> list[str]:
        """Return installed package names when a device is available."""
        return self.installed_packages()

    def resolve_package(self, app_name: str) -> str | None:
        """Resolve an app name only against packages installed on the device."""
        normalized = normalize_app_name(app_name)
        installed = self.installed_packages()
        if not installed:
            return None
        if normalized in installed:
            return normalized
        for hint in package_hints_for(normalized):
            if hint in installed:
                return hint

        compact = re.sub(r"[^a-z0-9]", "", normalized)
        candidates = [
            package for package in installed
            if compact and compact in re.sub(r"[^a-z0-9]", "", package.casefold())
        ]
        return candidates[0] if len(candidates) == 1 else None

    def close_app(self, app_name: str, *, package: str | None = None) -> AndroidOperationResult:
        """Force-stop only a package verified against installed packages."""
        requested = str(app_name or "").strip()
        resolved = package or self.resolve_package(requested)
        installed = self.installed_packages()
        if (
            not resolved
            or resolved not in installed
            or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)+", resolved)
        ):
            return AndroidOperationResult(False, "close_app", "The application package is invalid or not installed.")
        result = self.adb.shell(["am", "force-stop", resolved])
        return AndroidOperationResult(result.ok, "close_app", result.stderr.strip() or result.stdout.strip(), package=resolved)

    def foreground_package(self) -> str | None:
        result = self.adb.shell(["dumpsys", "activity", "activities"])
        if not result.ok:
            return None
        match = re.search(r"(?:mResumedActivity|ResumedActivity):.*?\s([A-Za-z][\w.]+)/(?:[\w.$]+)", result.stdout)
        return match.group(1) if match else None

    def go_home(self) -> AndroidOperationResult:
        ok = self.launch_intent(IntentSpec(ACTION_HOME, categories=(CATEGORY_HOME,)))
        return AndroidOperationResult(ok, "home", "" if ok else "Android did not accept the home intent.")

    def battery_status(self) -> BatteryStatus | None:
        result = self.adb.shell(["dumpsys", "battery"])
        if not result.ok:
            return None
        values: dict[str, str] = {}
        for line in result.stdout.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                values[key.strip().casefold()] = value.strip()

        def number(key: str, divisor: float = 1.0):
            try:
                return float(values[key]) / divisor
            except (KeyError, TypeError, ValueError):
                return None

        temperature = number("temperature", 10.0)
        voltage = number("voltage", 1000.0)
        level = number("level")
        percentage: int | float | None = None
        if level is not None:
            percentage = int(level) if level.is_integer() else level
        plugged = ", ".join(
            key.removesuffix(" powered")
            for key in ("ac powered", "usb powered", "wireless powered")
            if values.get(key, "").casefold() == "true"
        )
        return BatteryStatus(
            percentage=percentage,
            status=values.get("status", ""),
            plugged=plugged,
            health=values.get("health", ""),
            temperature_c=temperature,
            voltage_v=voltage,
        )

    def open_url(self, url: str, *, package: str | None = None) -> AndroidOperationResult:
        value = str(url).strip()
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https", "geo", "mailto", "tel"} or (
            parsed.scheme in {"http", "https"} and not parsed.netloc
        ):
            return AndroidOperationResult(False, "open_url", "The URL is invalid.")
        ok = self.launch_intent(IntentSpec("android.intent.action.VIEW", data=value, package=package))
        return AndroidOperationResult(ok, "open_url", "" if ok else "No Android activity accepted the URL.", package=package)

    def search_youtube(self, query: str) -> AndroidOperationResult:
        package = self.resolve_package("youtube")
        if not package:
            return AndroidOperationResult(False, "search_youtube", "YouTube is not installed.")
        return self.open_url(youtube_search_url(query), package=package)

    def search_web(self, query: str, provider: str = "google") -> AndroidOperationResult:
        return self.open_url(web_search_url(query, provider))

    def open_camera(self, facing: str | None = None) -> AndroidOperationResult:
        facing_name = str(facing or "").strip().casefold()
        if facing_name not in {"", "front", "rear"}:
            return AndroidOperationResult(False, "open_camera", "Camera must be front or rear.")
        try:
            companion_available = self.companion_available()
        except AdbError as error:
            return AndroidOperationResult(False, "open_camera", str(error), supported=False)
        if companion_available:
            return self._companion_operation("preview", facing_name or "rear")
        extras = () if not facing_name else (
            ("ei", "android.intent.extras.CAMERA_FACING", "1" if facing_name == "front" else "0"),
        )
        try:
            ok = self.launch_intent(IntentSpec("android.media.action.IMAGE_CAPTURE", extras=extras))
        except AdbError as error:
            return AndroidOperationResult(False, "open_camera", str(error), supported=False)
        detail = "" if ok else "The camera intent was not accepted; lens selection is app-specific."
        return AndroidOperationResult(ok, "open_camera", detail, supported=ok)

    def companion_available(self) -> bool:
        if not self.companion_package:
            return False
        result = self.adb.shell(["pm", "list", "packages", self.companion_package])
        return result.ok and f"package:{self.companion_package}" in result.stdout.split()

    def _companion_operation(self, operation: str, facing: str = "rear") -> AndroidOperationResult:
        """Run one operation in the installed Camera2 companion and verify its result."""
        request_id = uuid.uuid4().hex
        args = [
            "shell", "am", "start", "-W",
        ]
        if operation == "preview":
            # Preview is a persistent activity. Clear the previous companion
            # instance first so its onDestroy() releases Camera2 before the
            # next front/rear preview opens.
            args.extend(["--activity-clear-task"])
        args.extend([
            "-n", f"{self.companion_package}/.MainActivity",
            "--es", "action", operation,
            "--es", "facing", facing,
            "--es", "request_id", request_id,
        ])
        try:
            started = self.adb.run_adb(args)
            output = f"{started.stdout}\n{started.stderr}".casefold()
            if not started.ok or "error:" in output or "unable to resolve" in output:
                return AndroidOperationResult(False, operation, "The Android companion could not be started.", supported=False)
            deadline = time.monotonic() + min(self.adb.timeout, 10.0)
            while time.monotonic() < deadline:
                result = self.adb.shell([
                    "run-as", self.companion_package, "cat", "files/last_result.json",
                ])
                if result.ok:
                    try:
                        payload = json.loads(result.stdout)
                    except (TypeError, ValueError):
                        payload = {}
                    if payload.get("request_id") == request_id:
                        return AndroidOperationResult(
                            bool(payload.get("ok")), operation,
                            str(payload.get("message", "")),
                            package=payload.get("package"),
                            location=payload.get("location"),
                            supported=bool(payload.get("supported", True)),
                        )
                time.sleep(0.1)
            return AndroidOperationResult(False, operation, "The Android companion did not return a verified result.", supported=False)
        except AdbError as error:
            return AndroidOperationResult(False, operation, str(error), supported=False)

    def capture_photo(self, facing: str | None = None) -> AndroidOperationResult:
        facing_name = str(facing or "rear").strip().casefold()
        if facing_name not in {"front", "rear"}:
            return AndroidOperationResult(False, "capture_photo", "Camera must be front or rear.")
        try:
            companion_available = self.companion_available()
        except AdbError as error:
            return AndroidOperationResult(False, "capture_photo", str(error), supported=False)
        if not companion_available:
            return AndroidOperationResult(False, "capture_photo", "Verified photo capture requires the Android Camera2 companion app.", supported=False)
        return self._companion_operation("capture", facing_name)

    def flashlight(self, enabled: bool) -> AndroidOperationResult:
        try:
            companion_available = self.companion_available()
        except AdbError as error:
            return AndroidOperationResult(False, "flashlight", str(error), supported=False)
        if not companion_available:
            return AndroidOperationResult(False, "flashlight", "Verified flashlight control requires the Android Camera2 companion app.", supported=False)
        return self._companion_operation("flashlight_on" if enabled else "flashlight_off", "rear")

    def resolve_launcher_activity(self, package: str) -> str | None:
        result = self.adb.shell(
            [
                "cmd", "package", "resolve-activity", "--brief",
                "-a", ACTION_MAIN, "-c", CATEGORY_LAUNCHER, "-p", package,
            ]
        )
        if not result.ok:
            return None
        for line in reversed(result.stdout.splitlines()):
            value = line.strip()
            if "/" in value and not value.lower().startswith("priority"):
                return value
        return None

    def open_app(self, app_name: str) -> AppLaunchResult:
        """Open a standard Android target or an installed named package."""
        app_name = str(app_name).strip()
        if not app_name:
            return AppLaunchResult(False, app_name, error_code="invalid_app")
        try:
            standard_intent = standard_intent_for(app_name)
            if standard_intent is not None:
                success = self.launch_intent(standard_intent)
                return AppLaunchResult(
                    success, app_name, error_code=None if success else "launch_failed"
                )

            package = self.resolve_package(app_name)
            if not package:
                return AppLaunchResult(False, app_name, error_code="not_installed")

            # * Resolve the launcher from the installed package. Some Android
            # * component names contain '$'; passing those through ``adb shell
            # * -n`` can be interpreted by the remote shell, so those use the
            # * package-scoped launcher intent instead.
            launcher = self.resolve_launcher_activity(package)
            intent = IntentSpec(
                action=ACTION_MAIN,
                categories=(CATEGORY_LAUNCHER,) if launcher else (),
                package=package,
                component=(launcher if launcher and "$" not in launcher else None),
            )
            success = self.launch_intent(intent)
            return AppLaunchResult(
                success,
                app_name,
                package=package,
                error_code=None if success else "launch_failed",
            )
        except AdbError as error:
            return AppLaunchResult(
                False, app_name, error_code="bridge_unavailable", detail=str(error)
            )

    def device_status(self) -> DeviceStatus:
        adb_path = self.adb.adb_path
        adb_available = self.adb.is_available()
        if not adb_available:
            return DeviceStatus(False, adb_path)

        try:
            devices = tuple(self.get_devices())
        except AdbError as error:
            return DeviceStatus(adb_available, adb_path, error=str(error))
        selected = self.get_selected_device()
        model = ""
        android_version = ""
        if selected:
            try:
                model = self.adb.shell(["getprop", "ro.product.model"]).stdout.strip()
                android_version = self.adb.shell(
                    ["getprop", "ro.build.version.release"]
                ).stdout.strip()
            except AdbError:
                pass

        return DeviceStatus(
            adb_available, adb_path, devices, selected, model, android_version
        )

    def connection_status(self) -> AndroidConnectionStatus:
        """Return one UI-safe snapshot without exposing duplicate transport rows."""
        status = self.device_status()
        wireless_endpoints = tuple(
            device.serial
            for device in status.devices
            if device.is_online and device.is_wireless
        )
        selected = status.selected_device
        if selected is None:
            selected = next(
                (device for device in status.devices if device.is_online),
                None,
            )
            if self.adb.selected_device_id:
                selected = None
        if selected is None:
            return AndroidConnectionStatus(
                status.adb_available,
                status.adb_path,
                wireless_endpoints=wireless_endpoints,
                error=status.error,
            )

        model = status.model or selected.model or selected.product
        host, port = self.adb.endpoint_parts(selected.endpoint)
        return AndroidConnectionStatus(
            status.adb_available,
            status.adb_path,
            connected=True,
            selected_device=selected,
            model=model,
            android_version=status.android_version,
            connection_type=self.adb.connection_type(selected),
            endpoint=selected.endpoint,
            wireless_endpoints=wireless_endpoints,
            host=host,
            port=port,
        )
