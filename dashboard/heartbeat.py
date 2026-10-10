"""Windows desktop presence heartbeat for the JARVIS remote client."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from config.environment import get_env
from config.settings import VERSION


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DESKTOP_ID_FILE = PROJECT_ROOT / ".desktop_id"
HEARTBEAT_INTERVAL_SECONDS = 30
REQUEST_TIMEOUT_SECONDS = 10


def _get_desktop_id() -> str:
    """Read the persistent desktop ID, creating it once when necessary."""

    try:
        desktop_id = DESKTOP_ID_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        desktop_id = ""
    except OSError as error:
        # * An ID is still useful for this run if the project directory is not
        # * writable; the worker will continue without affecting JARVIS.
        print(f"[HEARTBEAT] Could not persist desktop ID: {error}")
        return str(uuid.uuid4())

    if desktop_id:
        return desktop_id

    desktop_id = str(uuid.uuid4())
    try:
        DESKTOP_ID_FILE.write_text(desktop_id + "\n", encoding="utf-8")
    except OSError as error:
        print(f"[HEARTBEAT] Could not persist desktop ID: {error}")
    return desktop_id


class HeartbeatService:
    """Best-effort background reporter for the Firebase presence endpoint."""

    def __init__(self, endpoint: str):
        self._endpoint = endpoint
        self._desktop_id = _get_desktop_id()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> bool:
        if self._thread is not None and self._thread.is_alive():
            return True

        try:
            self._thread = threading.Thread(
                target=self._run,
                name="jarvis-heartbeat",
                daemon=True,
            )
            self._thread.start()
            print("[HEARTBEAT] Started")
            return True
        except Exception as error:
            print(f"[HEARTBEAT] Could not start: {error}")
            self._thread = None
            return False

    def stop(self) -> None:
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=REQUEST_TIMEOUT_SECONDS + 1)
        self._thread = None
        print("[HEARTBEAT] Stopped")

    def _run(self) -> None:
        while not self._stop_event.is_set():
            self._send_heartbeat()
            self._stop_event.wait(HEARTBEAT_INTERVAL_SECONDS)

    def _send_heartbeat(self) -> None:
        payload = {
            "desktopId": self._desktop_id,
            "status": "ONLINE",
            "fcmToken": "",
            "androidDeviceId": "",
            "clientVersion": str(VERSION),
            "schemaVersion": "1",
        }

        request = urllib.request.Request(
            self._endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS):
                pass
            print("[HEARTBEAT] ONLINE heartbeat sent")
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            print(f"[HEARTBEAT] Network error: {error}")
        except Exception as error:
            # ! A malformed endpoint or unexpected client-side error must not
            # * terminate the worker or the main JARVIS process.
            print(f"[HEARTBEAT] Error: {error}")


_service: HeartbeatService | None = None
_service_lock = threading.Lock()


def start_heartbeat() -> bool:
    """Start the heartbeat if the project-local endpoint is configured."""

    global _service

    endpoint = get_env("FIREBASE_PRESENCE_URL").strip()
    if not endpoint:
       # print("[HEARTBEAT] FIREBASE_PRESENCE_URL is not configured; disabled")
        return False

    with _service_lock:
        if _service is None:
            _service = HeartbeatService(endpoint)
        return _service.start()


def stop_heartbeat() -> None:
    """Stop the heartbeat safely, including when it was never started."""

    global _service

    with _service_lock:
        service = _service
        _service = None

    if service is not None:
        try:
            service.stop()
        except Exception as error:
            print(f"[HEARTBEAT] Stop error: {error}")
