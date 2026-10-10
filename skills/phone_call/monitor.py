"""Read-only Android call-state monitor for the Phone Call skill."""

from __future__ import annotations

import os
import re
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from services.android import get_android_manager


IDLE = "IDLE"
RINGING = "RINGING"
ACTIVE = "ACTIVE"
DISCONNECTED = "DISCONNECTED"
OUTGOING_IDLE_GRACE_SECONDS = float(
    os.getenv("PHONE_CALL_OUTGOING_IDLE_GRACE", "8.0")
)


@dataclass(frozen=True)
class CallSnapshot:
    state: str = IDLE
    phone_number: str = ""
    caller_name: str = ""
    direction: str = ""
    started_at: float = 0.0
    active_started_at: float = 0.0


def parse_telephony_registry(output: str) -> CallSnapshot:
    """Parse only current telephony state fields from dumpsys output."""
    states = [
        int(value)
        for value in re.findall(r"\bmCallState=(\d+)\b", output or "")
    ]
    numeric_state = max(states, default=0)
    state = {0: IDLE, 1: RINGING, 2: ACTIVE}.get(numeric_state, IDLE)

    numbers = [
        value.strip()
        for value in re.findall(r"\bmCallIncomingNumber=(.*)", output or "")
        if value.strip()
    ]
    phone_number = numbers[-1] if numbers else ""
    return CallSnapshot(state=state, phone_number=phone_number)


class PhoneCallMonitor:
    """Poll the read-only telephony registry at a controlled interval."""

    def __init__(
        self,
        manager=None,
        poll_interval: float | None = None,
        announce=None,
        notify=None,
    ):
        self.manager = manager or get_android_manager()
        self.poll_interval = poll_interval or float(
            os.getenv("PHONE_CALL_POLL_INTERVAL", "3.0")
        )
        self._announce = announce or self._speak
        self._notify = notify or self._hud_notify
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.RLock()
        self._snapshot = CallSnapshot()
        self._last_transition = IDLE
        self._last_ended_at = 0.0
        self._ring_started_at_ms = 0
        self._outgoing_idle_since = 0.0

    @staticmethod
    def _speak(message: str) -> None:
        try:
            from voice.manager import speak

            speak(message)
        except Exception:
            pass

    @staticmethod
    def _hud_notify(message: str) -> None:
        try:
            from hud.integration import HUDIntegration

            HUDIntegration.notify(message)
        except Exception as error:
            print(f"[PHONE CALL] HUD notification failed: {error}")

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> bool:
        if self.running:
            return True
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="jarvis-phone-call-monitor",
            daemon=True,
        )
        self._thread.start()
        return True

    def stop(self) -> None:
        self._stop_event.set()
        thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout=max(1.0, self.poll_interval + 1.0))
        self._thread = None

    def _run(self) -> None:
        while not self._stop_event.wait(self.poll_interval):
            try:
                self.poll_once()
            except Exception as error:
                # ! ADB loss or a provider variation must not stop JARVIS.
                print(f"[PHONE CALL] Monitor check skipped: {error}")

    def _read_snapshot(self) -> CallSnapshot:
        device = self.manager.adb.select_device()
        if not device or not device.is_online:
            return CallSnapshot()
        result = self.manager.run_adb(
            ["shell", "dumpsys", "telephony.registry"],
            device=device.serial,
        )
        if not result.ok:
            return CallSnapshot()
        return parse_telephony_registry(result.stdout)

    def poll_once(self) -> CallSnapshot:
        observed = self._read_snapshot()
        return self.process_snapshot(observed)

    def begin_outgoing(self, phone_number: str, caller_name: str = "") -> CallSnapshot:
        """Publish CALLING before telephony confirms that the call is active."""
        with self._lock:
            snapshot = CallSnapshot(
                state="OUTGOING",
                phone_number=phone_number,
                caller_name=caller_name,
                direction="OUTGOING",
                started_at=time.time(),
            )
            self._snapshot = snapshot
            self._last_transition = "OUTGOING"
            self._emit_hud_state(
                "OUTGOING",
                snapshot,
                f"Calling {self._display_caller(snapshot)}.",
            )
            return snapshot

    def process_snapshot(self, observed: CallSnapshot) -> CallSnapshot:
        with self._lock:
            previous = self._snapshot
            if previous.state == "OUTGOING" and observed.state == IDLE:
                now = time.monotonic()
                if not self._outgoing_idle_since:
                    self._outgoing_idle_since = now
                if now - self._outgoing_idle_since < OUTGOING_IDLE_GRACE_SECONDS:
                    return previous
            else:
                self._outgoing_idle_since = 0.0

            if previous.state in {"OUTGOING", RINGING, ACTIVE} and observed.state == IDLE:
                ended = CallSnapshot(
                    state=DISCONNECTED,
                    phone_number=previous.phone_number,
                    caller_name=previous.caller_name,
                    direction=previous.direction,
                    started_at=previous.started_at,
                    active_started_at=previous.active_started_at,
                )
                self._snapshot = ended
                self._last_transition = DISCONNECTED
                self._last_ended_at = time.monotonic()
                self._emit_hud_state(
                    DISCONNECTED,
                    ended,
                    f"Call ended with {self._display_caller(previous)}.",
                )
                if previous.state == RINGING and self._call_log_confirms_missed(
                    self._ring_started_at_ms
                ):
                    caller = self._display_caller(previous)
                    self._announce(f"You missed a call from {caller}.")
                return ended

            if observed.state == previous.state and previous.state != IDLE:
                observed = CallSnapshot(
                    state=observed.state,
                    phone_number=observed.phone_number or previous.phone_number,
                    caller_name=observed.caller_name or previous.caller_name,
                    direction=observed.direction or previous.direction,
                    started_at=observed.started_at or previous.started_at,
                    active_started_at=(
                        observed.active_started_at or previous.active_started_at
                    ),
                )

            changed = observed.state != previous.state
            if observed.state == RINGING and previous.state != RINGING:
                caller_name = self._resolve_caller(observed.phone_number)
                observed = CallSnapshot(
                    state=RINGING,
                    phone_number=observed.phone_number,
                    caller_name=caller_name,
                    direction="INCOMING",
                    started_at=time.time(),
                )
                self._ring_started_at_ms = int(time.time() * 1000)
                caller = self._display_caller(observed)
                message = f"You have an incoming call from {caller}."
                self._announce(message)
                self._emit_hud_state(
                    RINGING,
                    observed,
                    f"📞 INCOMING CALL — {caller}",
                    event_type="PHONE_CALL_INCOMING",
                )
                changed = True
            elif observed.state == ACTIVE and previous.state != ACTIVE:
                observed = CallSnapshot(
                    state=ACTIVE,
                    phone_number=observed.phone_number or previous.phone_number,
                    caller_name=observed.caller_name or previous.caller_name,
                    direction=previous.direction or "INCOMING",
                    started_at=previous.started_at or time.time(),
                    active_started_at=time.time(),
                )
                self._emit_hud_state(
                    ACTIVE,
                    observed,
                    f"Call active with {self._display_caller(observed)}.",
                )
                changed = True

            elif observed.state == IDLE and previous.state == DISCONNECTED:
                # * Keep DISCONNECTED visible for one poll so the frontend can
                # * run its short exit animation, then return to IDLE.
                observed = CallSnapshot()
                changed = True

            self._snapshot = observed
            if changed:
                self._last_transition = observed.state
            return observed

    def _emit_hud_state(
        self,
        state: str,
        snapshot: CallSnapshot,
        message: str,
        event_type: str = "PHONE_CALL_STATUS",
    ) -> None:
        self._notify(message)
        try:
            from hud.integration import HUDIntegration

            HUDIntegration.system_activity(message)
        except Exception:
            pass
        try:
            from hud.integration import HUDIntegration

            HUDIntegration.system_update(
                {
                    "phone_call": {
                        "type": event_type,
                        "state": state.casefold(),
                        "direction": snapshot.direction,
                        "caller_name": snapshot.caller_name,
                        "phone_number": snapshot.phone_number,
                        "started_at": snapshot.active_started_at
                        or snapshot.started_at
                        or None,
                        "timestamp": datetime.now(timezone.utc).isoformat(
                            timespec="milliseconds"
                        ),
                    }
                }
            )
        except Exception:
            # ! HUD availability must never affect call-state monitoring.
            pass

    def _call_log_confirms_missed(self, ring_started_at_ms: int) -> bool:
        """Confirm a missed call from the read-only call log when available."""
        if not ring_started_at_ms:
            return False
        try:
            device = self.manager.adb.select_device()
            if not device or not device.is_online:
                return False
            result = self.manager.run_adb(
                [
                    "shell",
                    "content",
                    "query",
                    "--uri",
                    "content://call_log/calls",
                    "--where",
                    "type=3",
                    "--sort",
                    "date DESC",
                ],
                device=device.serial,
            )
            if not result.ok:
                return False
            match = re.search(r"\bdate=(\d+)\b", result.stdout)
            return bool(match and int(match.group(1)) >= ring_started_at_ms - 5000)
        except Exception:
            return False

    def _resolve_caller(self, phone_number: str) -> str:
        if not phone_number:
            return ""
        try:
            from .phone_call import _numbers_match, query_phone_contacts

            contacts = query_phone_contacts() or []
            matches = [
                contact
                for contact in contacts
                if _numbers_match(contact.get("number", ""), phone_number)
            ]
            names = {contact.get("name", "").strip() for contact in matches}
            return next(iter(names)) if len(names) == 1 else ""
        except Exception:
            return ""

    @staticmethod
    def _display_caller(snapshot: CallSnapshot) -> str:
        if snapshot.caller_name:
            try:
                from .phone_call import _spoken_contact_name

                return _spoken_contact_name(snapshot.caller_name)
            except Exception:
                return snapshot.caller_name
        if snapshot.phone_number:
            return snapshot.phone_number
        return "an unknown number"

    def status_message(self) -> str:
        with self._lock:
            snapshot = self._snapshot
            if snapshot.state == "OUTGOING":
                return f"Calling {self._display_caller(snapshot)}."
            if snapshot.state == RINGING:
                return f"Incoming call from {self._display_caller(snapshot)}."
            if snapshot.state == ACTIVE:
                return f"Call active with {self._display_caller(snapshot)}."
            if (
                self._last_transition == DISCONNECTED
                and time.monotonic() - self._last_ended_at < 30
            ):
                return "Call ended."
            return "No active call."


_monitor: PhoneCallMonitor | None = None
_monitor_lock = threading.Lock()


def get_call_monitor() -> PhoneCallMonitor:
    global _monitor
    with _monitor_lock:
        if _monitor is None:
            _monitor = PhoneCallMonitor()
        return _monitor


def start_phone_call_monitor() -> PhoneCallMonitor:
    monitor = get_call_monitor()
    monitor.start()
    return monitor


def stop_phone_call_monitor() -> None:
    monitor = _monitor
    if monitor is not None:
        monitor.stop()
