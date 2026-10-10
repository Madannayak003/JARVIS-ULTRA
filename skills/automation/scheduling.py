"""Persistent, lifecycle-managed scheduling for trusted JARVIS commands."""

from __future__ import annotations

import json
import os
import tempfile
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from core.registry import register
from core.notifications import notify_windows_toast
from hud.integration import HUDIntegration
from voice.manager import speak
from core.diagnostics import debug_print

DATA_FILE = Path("data") / "schedules.json"
_lock = threading.RLock()
_worker_thread: threading.Thread | None = None
_stop_event = threading.Event()
_started = False
_executor: Callable[[str], Any] | None = None
_inflight_ids: set[int] = set()


def _load() -> list[dict[str, Any]]:
    if not DATA_FILE.exists():
        return []
    try:
        value = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return value if isinstance(value, list) else []
    except (OSError, json.JSONDecodeError) as error:
        print(f"[SCHEDULER] Load failed: {error}")
        return []


def _save(items: list[dict[str, Any]]) -> bool:
    temporary_path = None
    try:
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=DATA_FILE.parent,
            prefix=f".{DATA_FILE.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = temporary_file.name
            json.dump(items, temporary_file, indent=2, ensure_ascii=False)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, DATA_FILE)
        return True
    except OSError as error:
        print(f"[SCHEDULER] Save failed: {error}")
        return False
    finally:
        if temporary_path:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass


def _parse(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _next_daily(target: datetime, now: datetime) -> datetime:
    while target <= now:
        target += timedelta(days=1)
    return target


def create_schedule(data: dict[str, Any] | None = None):
    data = data or {}
    command = str(data.get("command", "")).strip()
    run_at = _parse(str(data.get("run_at", "")).strip())
    recurrence = str(data.get("recurrence", "none")).strip().lower()
    if not command or run_at is None:
        speak("I need a task and a valid schedule time.")
        return False
    if recurrence not in {"none", "daily"}:
        speak("Only one-time and daily schedules are supported.")
        return False
    with _lock:
        items = _load()
        next_id = max((int(item.get("id", 0)) for item in items), default=0) + 1
        item = {"id": next_id, "command": command, "run_at": run_at.isoformat(),
                "next_run_at": run_at.isoformat(), "recurrence": recurrence,
                "enabled": True, "created_at": datetime.now().isoformat()}
        items.append(item)
        if not _save(items):
            return False
    speak(f"Scheduled task {next_id}.")
    return item


def list_schedules(data: dict[str, Any] | None = None):
    return _load()


def cancel_schedule(data: dict[str, Any] | None = None):
    try:
        schedule_id = int((data or {}).get("id"))
    except (TypeError, ValueError):
        return False
    with _lock:
        items = _load()
        found = next((item for item in items if int(item.get("id", -1)) == schedule_id), None)
        if found is None:
            return False
        found["enabled"] = False
        found["cancelled_at"] = datetime.now().isoformat()
        return _save(items)


def set_executor(executor: Callable[[str], Any] | None) -> None:
    global _executor
    _executor = executor


def _advance(item: dict[str, Any], now: datetime) -> None:
    target = _parse(str(item.get("next_run_at", "")))
    if target is None:
        item["enabled"] = False
    elif item.get("recurrence") == "daily":
        item["next_run_at"] = _next_daily(target, now).isoformat()
    else:
        item["enabled"] = False
        item["completed_at"] = now.isoformat()


def _run_due() -> None:
    now = datetime.now()
    with _lock:
        items = _load()
        due = []
        changed = False
        for item in items:
            if not item.get("enabled", True):
                continue
            schedule_id = int(item.get("id", -1))
            if schedule_id in _inflight_ids:
                continue
            target = _parse(str(item.get("next_run_at", "")))
            if target is not None and target <= now:
                due.append(dict(item))
                _inflight_ids.add(schedule_id)
                if item.get("recurrence") == "daily":
                    _advance(item, now)
                    item["last_run_at"] = now.isoformat()
                changed = True
        if changed:
            _save(items)
    for item in due:
        command = str(item.get("command", "")).strip()
        schedule_id = int(item.get("id", -1))
        try:
            notify_windows_toast("J.A.R.V.I.S Scheduled Task", command)
            executor = _executor
            if executor is None:
                from core.dispatcher import dispatch
                executor = dispatch
            executor(command)
            if item.get("recurrence") != "daily":
                with _lock:
                    current_items = _load()
                    current = next((candidate for candidate in current_items if int(candidate.get("id", -1)) == schedule_id), None)
                    if current is not None and current.get("enabled", True):
                        current["enabled"] = False
                        current["completed_at"] = datetime.now().isoformat()
                        current["last_run_at"] = datetime.now().isoformat()
                        _save(current_items)
            HUDIntegration.notify("TASK COMPLETED", command, level="SUCCESS", source="scheduler", metadata={"schedule_id": schedule_id})
        except Exception as error:
            print(f"[SCHEDULER] Task {schedule_id} failed: {error}")
            HUDIntegration.notify("TASK FAILED", str(error), level="ERROR", source="scheduler", metadata={"schedule_id": schedule_id})
        finally:
            with _lock:
                _inflight_ids.discard(schedule_id)


def _worker() -> None:
    debug_print("[SCHEDULER] Background scheduler started")
    while not _stop_event.is_set():
        try:
            _run_due()
        except Exception as error:
            print(f"[SCHEDULER] Worker error: {error}")
        _stop_event.wait(1.0)


def start_scheduler() -> bool:
    global _started, _worker_thread
    with _lock:
        if _started and _worker_thread and _worker_thread.is_alive():
            return False
        _stop_event.clear()
        _worker_thread = threading.Thread(target=_worker, name="JarvisScheduler", daemon=True)
        _worker_thread.start()
        _started = True
        return True


def stop_scheduler() -> None:
    global _started, _worker_thread
    with _lock:
        if not _started:
            return
        _stop_event.set()
        thread = _worker_thread
    if thread and thread.is_alive():
        thread.join(timeout=2.0)
    with _lock:
        _worker_thread = None
        _started = False


def scheduler_started() -> bool:
    return _started


register("create_schedule", create_schedule, category="scheduling")
register("list_schedules", list_schedules, category="scheduling")
register("cancel_schedule", cancel_schedule, category="scheduling")
