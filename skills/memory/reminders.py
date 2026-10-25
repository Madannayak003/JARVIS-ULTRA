"""
JARVIS ULTRA
Reminders Skill

Handles personal reminders and stores them in JSON.
"""

import json
import threading
import time
from pathlib import Path
from core.registry import register
from core.notifications import notify_windows_toast
from core.diagnostics import debug_print
from core.reminder_time import (
    ReminderTimeError,
    local_now,
    normalize_stored_datetime,
    resolve_reminder_time,
)
from hud.integration import HUDIntegration
from core.live_execution import is_live_execution


def speak(text):
    """Load the legacy foreground voice path only when it is actually used."""
    from voice.manager import speak as _speak
    return _speak(text)


# * =========================================================
# * Storage
# * =========================================================

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

REMINDERS_FILE = DATA_DIR / "reminders.json"
_REMINDERS_LOCK = threading.RLock()


# * =========================================================
# * Storage Helpers
# * =========================================================

def _load_reminders():

    if not REMINDERS_FILE.exists():
        return []

    try:

        with open(
            REMINDERS_FILE,
            "r",
            encoding="utf-8",
        ) as f:

            data = json.load(f)

        if isinstance(data, list):
            return data

    except Exception as e:

        print(
            f"[REMINDERS ERROR] Load failed: {e}"
        )

    return []


def _save_reminders(reminders):

    try:

        with open(
            REMINDERS_FILE,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                reminders,
                f,
                indent=4,
                ensure_ascii=False,
            )

        return True

    except Exception as e:

        print(
            f"[REMINDERS ERROR] Save failed: {e}"
        )

        return False


# * =========================================================
# * Create Reminder
# * =========================================================

def create_reminder(data=None):

    data = data or {}
    reference_now = local_now()

    text = str(
        data.get("text", "")
    ).strip()

    remind_at = str(
        data.get("remind_at", "")
    ).strip()

    if not text:

        speak(
            "What should I remind you about?"
        )

        return False

    if not remind_at:

        speak(
            "When should I remind you?"
        )

        return False

    # * Resolve once from the same captured local reference used for storage.
    try:
        target = resolve_reminder_time(remind_at, now=reference_now)
    except ReminderTimeError as error:

        print(
            f"[REMINDERS ERROR] Invalid reminder time: {error}"
        )

        speak(
            "That reminder time is invalid or already past. Please give me a future time."
        )

        return False

    invocation_id = str(data.get("_invocation_id", "")).strip() or None

    with _REMINDERS_LOCK:
        reminders = _load_reminders()

        if invocation_id:
            for existing in reminders:
                if existing.get("invocation_id") == invocation_id:
                    existing_target = normalize_stored_datetime(existing.get("remind_at"))
                    speak(
                        f"That reminder is already scheduled for "
                        f"{existing_target.strftime('%A, %B %d at %I:%M %p').replace(' 0', ' ')}."
                    )
                    if is_live_execution():
                        return {
                            "ok": True,
                            "status": "already_exists",
                            "action": "create_reminder",
                            "item": dict(existing),
                        }
                    return True

        # * Generate ID
        if reminders:

            reminder_id = max(
                int(item.get("id", 0))
                for item in reminders
            ) + 1

        else:

            reminder_id = 1

        reminder = {
            "id": reminder_id,
            "text": text,
            "remind_at": target.isoformat(),
            "completed": False,
            "created_at": reference_now.isoformat(),
        }
        if invocation_id:
            reminder["invocation_id"] = invocation_id

        reminders.append(reminder)

        if not _save_reminders(reminders):

            speak(
                "I couldn't save that reminder."
            )

            return False

    print(
        f"[REMINDERS] Saved: "
        f"#{reminder_id} {text} -> {target.isoformat()}"
    )

    display = target.strftime("%A, %B %d at %I:%M %p").replace(" 0", " ")
    speak(f"I'll remind you on {display}.")

    if is_live_execution():
        return {
            "ok": True,
            "status": "reported_success",
            "action": "create_reminder",
            "item": dict(reminder),
        }
    return True


# * =========================================================
# * List Reminders
# * =========================================================

def list_reminders(data=None):

    with _REMINDERS_LOCK:
        reminders = _load_reminders()

    active = [
        item
        for item in reminders
        if not item.get("completed", False)
    ]

    if not active:

        speak(
            "You don't have any active reminders."
        )

        return {"ok": True, "status": "no_results", "action": "list_reminders", "items": [], "count": 0}

    print("\n[REMINDERS]")

    for reminder in active:

        print(
            f"{reminder.get('id')}. "
            f"{reminder.get('text')} "
            f"-> {reminder.get('remind_at')}"
        )

    speak(
        f"You have {len(active)} active reminders."
    )

    return {
        "ok": True,
        "status": "reported_success",
        "action": "list_reminders",
        "items": active,
        "count": len(active),
    }


def get_active_reminders(now=None):
    """Return active reminders due on the supplied local date, without TTS."""
    current = local_now(now)
    result = []
    for item in _load_reminders():
        if item.get("completed", False):
            continue
        try:
            target = normalize_stored_datetime(item.get("remind_at"))
        except ReminderTimeError:
            continue
        if target.astimezone(current.tzinfo).date() == current.date():
            result.append(item)
    return result


# * =========================================================
# * Cancel Reminder
# * =========================================================

def cancel_reminder(data=None):

    data = data or {}

    reminder_id = data.get("id")

    try:

        reminder_id = int(reminder_id)

    except Exception:

        speak(
            "I need the reminder number to cancel it."
        )

        return False

    with _REMINDERS_LOCK:
        reminders = _load_reminders()
        found = False
        for reminder in reminders:
            if int(reminder.get("id", -1)) == reminder_id:
                reminder["completed"] = True
                found = True
                break

        if found:
            saved = _save_reminders(reminders)
        else:
            saved = False

    if not found:

        speak(
            f"I couldn't find reminder {reminder_id}."
        )

        return False

    if not saved:

        speak(
            "I couldn't update the reminder."
        )

        return False

    print(
        f"[REMINDERS] Cancelled: #{reminder_id}"
    )

    speak(
        f"Reminder {reminder_id} cancelled."
    )

    return True


def delete_reminder(data=None):
    """Permanently remove one reminder from Schedule Center."""
    try:
        reminder_id = int((data or {}).get("id"))
    except (TypeError, ValueError):
        return False
    with _REMINDERS_LOCK:
        reminders = _load_reminders()
        remaining = [item for item in reminders if int(item.get("id", -1)) != reminder_id]
        if len(remaining) == len(reminders):
            return False
        return _save_reminders(remaining)


# * =========================================================
# * Reminder Worker
# * =========================================================

def _process_due_reminders(now=None):
    """Atomically mark due reminders complete and return pending deliveries."""
    reference_now = local_now(now)
    deliveries = []
    with _REMINDERS_LOCK:
        reminders = _load_reminders()
        changed = False
        for reminder in reminders:
            if reminder.get("completed", False):
                continue
            try:
                target = normalize_stored_datetime(reminder.get("remind_at"))
            except ReminderTimeError:
                continue
            if target <= reference_now:
                text = reminder.get("text", "your reminder")
                reminder["completed"] = True
                reminder["triggered_at"] = reference_now.isoformat()
                deliveries.append((reminder.get("id"), text))
                changed = True
        if changed and not _save_reminders(reminders):
            return []
    return deliveries


def _deliver_reminder_notifications(deliveries):
    """Deliver persisted reminder events without entering the TTS path."""
    for reminder_id, text in deliveries:
        print(f"[REMINDERS] Triggered: #{reminder_id} {text}")
        try:
            HUDIntegration.notify(
                "J.A.R.V.I.S Reminder",
                text,
                level="REMINDER",
                source="reminder",
                metadata={"id": reminder_id},
            )
        except Exception as error:
            debug_print("[REMINDERS] HUD notification failed:", type(error).__name__)
        notify_windows_toast("J.A.R.V.I.S Reminder", text)


def _reminder_worker():

    debug_print(
        "[REMINDERS] Background scheduler started"
    )

    while not _scheduler_stop.is_set():

        try:
            _deliver_reminder_notifications(_process_due_reminders())
        except Exception as e:
            print(f"[REMINDERS ERROR] Worker: {e}")

        _scheduler_stop.wait(1)


# * =========================================================
# * Start Scheduler
# * =========================================================

_scheduler_started = False
_scheduler_lock = threading.Lock()
_scheduler_stop = threading.Event()
_scheduler_thread = None


def _start_scheduler():

    global _scheduler_started, _scheduler_thread

    with _scheduler_lock:

        if _scheduler_started:
            return

        _scheduler_stop.clear()
        thread = threading.Thread(
            target=_reminder_worker,
            daemon=True,
            name="ReminderScheduler",
        )

        thread.start()
        _scheduler_thread = thread

        _scheduler_started = True


def start_scheduler():
    _start_scheduler()


def stop_scheduler():
    global _scheduler_started, _scheduler_thread
    with _scheduler_lock:
        if not _scheduler_started:
            return
        _scheduler_stop.set()
        thread = _scheduler_thread
        _scheduler_thread = None
        _scheduler_started = False
    if thread and thread.is_alive():
        thread.join(timeout=2.0)


# * =========================================================
# * Registry
# * =========================================================

register(
    "create_reminder",
    create_reminder,
)

register(
    "list_reminders",
    list_reminders,
)

register(
    "cancel_reminder",
    cancel_reminder,
)
