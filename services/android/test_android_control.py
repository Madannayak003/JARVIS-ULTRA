from types import SimpleNamespace

from core.live_agent import LIVE_CAPABILITY_SCHEMAS, _validate_structured_parameters
from core.routers.android_router import android_route
from services.android.adb_client import AdbClient
from services.android.adb_client import AdbError
from services.android.android_intents import web_search_url, youtube_search_url
from services.android.device_manager import AndroidDeviceManager
from services.android.models import AdbCommandResult


class FakeAdb:
    selected_device_id = "192.168.31.20:32905"
    adb_path = "adb"
    timeout = 2.0

    def __init__(self, battery="", companion=False, companion_ok=True):
        self.battery = battery
        self.companion = companion
        self.companion_ok = companion_ok
        self.request_id = ""
        self.calls = []

    def shell(self, args, **kwargs):
        self.calls.append(tuple(args))
        if args[:3] == ["pm", "list", "packages"]:
            packages = "package:com.google.android.youtube\npackage:com.snapchat.android"
            if self.companion: packages += "\npackage:com.jarvis.androidcontrol"
            return AdbCommandResult(("adb",), 0, packages)
        if args[:3] == ["run-as", "com.jarvis.androidcontrol", "cat"]:
            return AdbCommandResult(("adb",), 0, '{"ok": %s, "request_id": "%s", "location": "content://photo/1"}' % (str(self.companion_ok).lower(), self.request_id))
        if args[:2] == ["dumpsys", "battery"]:
            return AdbCommandResult(("adb",), 0, self.battery)
        return AdbCommandResult(("adb",), 0, "Starting: Intent")

    def run_adb(self, args, **kwargs):
        self.calls.append(tuple(args))
        if "request_id" in args:
            self.request_id = args[args.index("request_id") + 1]
        return AdbCommandResult(("adb",), 0, "Starting: Intent")


def test_explicit_wireless_selection_and_transport():
    def runner(command, **kwargs):
        return SimpleNamespace(returncode=0, stdout="List of devices attached\nUSB123\tdevice\n192.168.31.20:32905\tdevice\n", stderr="")
    client = AdbClient(adb_path="adb", device_id="192.168.31.20:32905", runner=runner)
    assert [item.connection_type for item in client.get_devices()] == ["USB", "Wireless"]
    assert client.select_device().serial == "192.168.31.20:32905"
    assert "192.168.31.20:32905" in client.run_adb(["shell", "true"]).command


def test_app_resolution_force_stop_and_provider_urls():
    fake = FakeAdb()
    manager = AndroidDeviceManager(fake)
    assert manager.resolve_package("Snapchat") == "com.snapchat.android"
    closed = manager.close_app("Snapchat")
    assert closed.success and closed.package == "com.snapchat.android"
    assert ("am", "force-stop", "com.snapchat.android") in fake.calls
    assert not manager.close_app("missing").success
    assert youtube_search_url("cats & dogs").endswith("cats+%26+dogs")
    assert web_search_url("weather", "bing").startswith("https://www.bing.com/search?q=")


def test_battery_and_camera_are_parsed_without_inventing_results():
    fake = FakeAdb("AC powered: false\nUSB powered: true\nlevel: 68\nstatus: 2\nhealth: 2\ntemperature: 321\nvoltage: 4100\n")
    battery = AndroidDeviceManager(fake).battery_status()
    assert battery.percentage == 68 and battery.plugged == "usb"
    assert battery.temperature_c == 32.1 and battery.voltage_v == 4.1
    manager = AndroidDeviceManager(fake)
    assert manager.open_camera("front").success
    assert ("--ei", "android.intent.extras.CAMERA_FACING", "1") == fake.calls[-1][-3:]
    assert not manager.open_camera("side").success


def test_android_routing_and_live_validation_contracts():
    assert android_route("check phone battery") == [{"action": "android_battery_status"}]
    assert android_route("search youtube for jazz") == [{"action": "android_search_youtube", "query": "jazz"}]
    assert "android_flashlight_on" in LIVE_CAPABILITY_SCHEMAS
    payload, error = _validate_structured_parameters("android_open_app", {"app": "Snapchat"})
    assert payload == {"app": "Snapchat"} and error is None
    assert _validate_structured_parameters("android_open_app", {"app": ""})[1]["status"] == "invalid_arguments"


def test_companion_flashlight_and_photo_results_are_verified():
    fake = FakeAdb(companion=True, companion_ok=True)
    manager = AndroidDeviceManager(fake)
    assert manager.flashlight(True).success
    photo = manager.capture_photo("front")
    assert photo.success and photo.location == "content://photo/1"

    failed = AndroidDeviceManager(FakeAdb(companion=True, companion_ok=False)).capture_photo("rear")
    assert not failed.success
    unsupported = AndroidDeviceManager(FakeAdb()).flashlight(True)
    assert not unsupported.success and unsupported.supported is False


def test_preview_uses_companion_ready_result_and_replaces_persistent_session():
    fake = FakeAdb(companion=True)
    manager = AndroidDeviceManager(fake)

    assert manager.open_camera("front").success
    first = fake.calls[-2]
    assert "--activity-clear-task" in first
    assert "--activity-new-task" not in first
    assert ("--es", "action", "preview") == tuple(first[first.index("--es"):first.index("--es") + 3])
    assert ("--es", "facing", "front") == tuple(first[first.index("--es", first.index("--es") + 1):first.index("--es", first.index("--es") + 1) + 3])

    assert manager.open_camera("rear").success
    second = fake.calls[-2]
    assert ("--es", "facing", "rear") == tuple(second[second.index("--es", second.index("--es") + 1):second.index("--es", second.index("--es") + 1) + 3])


def test_preview_failed_companion_launch_is_not_reported_as_success():
    class FailedLaunchAdb(FakeAdb):
        def run_adb(self, args, **kwargs):
            self.calls.append(tuple(args))
            return AdbCommandResult(("adb",), 1, stderr="Error: Activity not started")

    result = AndroidDeviceManager(FailedLaunchAdb(companion=True)).open_camera("front")
    assert not result.success
    assert result.supported is False


def test_companion_ignores_stale_result_files():
    class StaleThenCurrentAdb(FakeAdb):
        reads = 0

        def shell(self, args, **kwargs):
            if args[:3] == ["run-as", "com.jarvis.androidcontrol", "cat"]:
                self.reads += 1
                request_id = "stale-request" if self.reads == 1 else self.request_id
                return AdbCommandResult(
                    ("adb",), 0,
                    '{"ok": true, "request_id": "%s", "location": "content://photo/1"}' % request_id,
                )
            return super().shell(args, **kwargs)

    fake = StaleThenCurrentAdb(companion=True)
    result = AndroidDeviceManager(fake).capture_photo("rear")
    assert result.success
    assert fake.reads >= 2


def test_companion_operations_report_adb_disconnects_truthfully():
    class DisconnectedAdb(FakeAdb):
        def shell(self, args, **kwargs):
            raise AdbError("ADB device disconnected.")

    manager = AndroidDeviceManager(DisconnectedAdb())
    for result in (manager.flashlight(True), manager.capture_photo("rear"), manager.open_camera("front")):
        assert not result.success
        assert result.supported is False
        assert "disconnected" in result.detail.lower()
