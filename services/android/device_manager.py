"""Higher-level, still generic Android device and app primitives."""

from __future__ import annotations

import re
from typing import Sequence

from .adb_client import AdbClient, AdbError, normalize_endpoint
from .android_intents import (
    ACTION_MAIN,
    CATEGORY_LAUNCHER,
    normalize_app_name,
    package_hints_for,
    standard_intent_for,
)
from .models import AndroidConnectionStatus, AppLaunchResult, DeviceStatus, IntentSpec


class AndroidDeviceManager:
    """Reusable bridge operations shared by independent skills."""

    def __init__(self, adb_client: AdbClient | None = None):
        self.adb = adb_client or AdbClient()

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
            self.adb.select_device(endpoint)
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

        devices = tuple(self.get_devices())
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
        if selected is None:
            return AndroidConnectionStatus(
                status.adb_available,
                status.adb_path,
                wireless_endpoints=wireless_endpoints,
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
