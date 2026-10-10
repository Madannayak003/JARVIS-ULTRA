"""
JARVIS PRO
Reminders Skill

Handles personal reminders and stores them in JSON.
"""

import json
import threading
import time
from pathlib import Path
from datetime import datetime

from core.registry import register
from voice.manager import speak
from core.notifications import notify_windows_toast
from core.diagnostics import debug_print


# * =========================================================
# * Storage
# * =========================================================

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

REMINDERS_FILE = DATA_DIR / "reminders.json"


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

    # * Validate datetime
    try:

        target = datetime.fromisoformat(
            remind_at
        )

    except Exception:

        print(
            f"[REMINDERS ERROR] Invalid datetime: {remind_at}"
        )

        speak(
            "I couldn't understand that reminder time."
        )

        return False

    reminders = _load_reminders()

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
        "created_at": datetime.now().isoformat(),
    }

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

    speak(
        f"I'll remind you at {target.strftime('%I:%M %p').lstrip('0')}."
    )

    return True


# * =========================================================
# * List Reminders
# * =========================================================

def list_reminders(data=None):

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

        return True

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

    return True


def get_active_reminders(now=None):
    """Return active reminders due on the supplied local date, without TTS."""
    current = now or datetime.now()
    result = []
    for item in _load_reminders():
        if item.get("completed", False):
            continue
        try:
            target = datetime.fromisoformat(str(item.get("remind_at", "")))
        except ValueError:
            continue
        if target.date() == current.date():
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

    reminders = _load_reminders()

    found = False

    for reminder in reminders:

        if int(reminder.get("id", -1)) == reminder_id:

            reminder["completed"] = True
            found = True
            break

    if not found:

        speak(
            f"I couldn't find reminder {reminder_id}."
        )

        return False

    if not _save_reminders(reminders):

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


# * =========================================================
# * Reminder Worker
# * =========================================================

def _reminder_worker():

    debug_print(
        "[REMINDERS] Background scheduler started"
    )

    while not _scheduler_stop.is_set():

        try:

            reminders = _load_reminders()

            now = datetime.now()

            changed = False

            for reminder in reminders:

                if reminder.get("completed", False):
                    continue

                remind_at = reminder.get("remind_at")

                if not remind_at:
                    continue

                try:

                    target = datetime.fromisoformat(
                        remind_at
                    )

                except Exception:

                    continue

                if target <= now:

                    text = reminder.get(
                        "text",
                        "your reminder",
                    )

                    print(
                        f"[REMINDERS] Triggered: "
                        f"#{reminder.get('id')} {text}"
                    )

                    speak(
                        f"Reminder: {text}"
                    )

                    notify_windows_toast(
                        "J.A.R.V.I.S Reminder",
                        text,
                    )

                    reminder["completed"] = True

                    reminder["triggered_at"] = (
                        datetime.now().isoformat()
                    )

                    changed = True

            if changed:

                _save_reminders(reminders)

        except Exception as e:

            print(
                f"[REMINDERS ERROR] Worker: {e}"
            )

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
