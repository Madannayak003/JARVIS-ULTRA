import re
from datetime import datetime, timedelta


def _clock(value: str, tomorrow: bool = False) -> datetime | None:
    cleaned = value.replace(".", "").upper().strip()

    for fmt in ("%I:%M %p", "%I %p"):
        try:
            parsed = datetime.strptime(cleaned, fmt)
            break
        except ValueError:
            parsed = None

    if parsed is None:
        return None

    now = datetime.now()
    target = now.replace(
        hour=parsed.hour,
        minute=parsed.minute,
        second=0,
        microsecond=0,
    )

    if tomorrow or target <= now:
        target += timedelta(days=1)

    return target


def schedule_route(command: str):
    # * Remove normal sentence-ending punctuation.
    command = re.sub(r"[.!?]+$", "", command.strip())

    # * ---------------------------------------------------------
    # * Relative schedules
    #
    # * Supported:
    # * schedule a task to open Chrome in 1 minute
    # * schedule a task to open Chrome after 1 minute
    # * schedule a task to open Chrome at 1 minute from now
    # * schedule a task to open Chrome 1 minute from now
    # * schedule a task to open Chrome at 1 minute
    # * ---------------------------------------------------------
    relative = re.match(
        r"^schedule\s+(?:a\s+)?task\s+(?:to\s+)?(.+?)\s+"
        r"(?:in|after|at\s+)?\s*"
        r"(\d+)\s+"
        r"(second|seconds|minute|minutes|hour|hours)"
        r"(?:\s+from\s+now)?$",
        command,
        re.IGNORECASE,
    )

    if relative:
        task, amount_text, unit = relative.groups()

        amount = int(amount_text)

        seconds = amount * {
            "second": 1,
            "seconds": 1,
            "minute": 60,
            "minutes": 60,
            "hour": 3600,
            "hours": 3600,
        }[unit.lower()]

        return [{
            "action": "create_schedule",
            "command": task.strip(),
            "run_at": (
                datetime.now() + timedelta(seconds=seconds)
            ).isoformat(),
            "recurrence": "none",
        }]

    # * ---------------------------------------------------------
    # * Specific-time schedules
    #
    # * Supported:
    # * schedule a task at 10 PM to open Chrome
    # * schedule a task tomorrow at 10 PM to open Chrome
    # * schedule a task every day at 10 PM to open Chrome
    # * ---------------------------------------------------------
    match = re.match(
        r"^schedule\s+(?:a\s+)?task\s+(?:(every\s+day)\s+)?"
        r"(?:(tomorrow)\s+)?at\s+"
        r"(\d{1,2}(?::\d{2})?\s*[ap]\.?m\.?)\s+"
        r"(?:to\s+)?(.+)$",
        command,
        re.IGNORECASE,
    )

    if match:
        recurring, tomorrow, time_text, task = match.groups()

        target = _clock(
            time_text,
            bool(tomorrow),
        )

        if target and task.strip():
            return [{
                "action": "create_schedule",
                "command": task.strip(),
                "run_at": target.isoformat(),
                "recurrence": "daily" if recurring else "none",
            }]

    # * ---------------------------------------------------------
    # * List schedules
    # * ---------------------------------------------------------
    if command.lower() in {
        "show my scheduled tasks",
        "list scheduled tasks",
        "what's scheduled for today",
        "whats scheduled for today",
    }:
        return [{
            "action": "list_schedules"
        }]

    # * ---------------------------------------------------------
    # * Cancel/delete schedule
    # * ---------------------------------------------------------
    match = re.match(
        r"^(?:cancel|delete)\s+"
        r"(?:scheduled\s+task\s+)?"
        r"(?:number\s+)?(\d+)$",
        command,
        re.IGNORECASE,
    )

    if match:
        return [{
            "action": "cancel_schedule",
            "id": int(match.group(1)),
        }]

    return None