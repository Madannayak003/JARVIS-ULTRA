"""Timezone-aware, deterministic reminder time resolution."""

from __future__ import annotations

import re
from datetime import date, datetime, time as time_type, timedelta
from typing import Any


class ReminderTimeError(ValueError):
    """Raised when a reminder time is missing, invalid, ambiguous, or past."""


_RELATIVE_RE = re.compile(
    r"^(?:in\s+|after\s+)?(?P<amount>\d+)\s*"
    r"(?P<unit>seconds?|secs?|minutes?|mins?|hours?|hrs?)"
    r"(?:\s+from\s+now)?$",
    re.IGNORECASE,
)
_CLOCK_RE = re.compile(
    r"^(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?\s*"
    r"(?P<ampm>a\.?m\.?|p\.?m\.?)?$",
    re.IGNORECASE,
)
_DATE_CLOCK_RE = re.compile(
    r"^(?P<day>\d{4}-\d{2}-\d{2})\s+(?:at\s+)?(?P<clock>.+)$",
    re.IGNORECASE,
)


def local_timezone():
    """Return the operating system's current local timezone."""
    return datetime.now().astimezone().tzinfo


def local_now(reference: datetime | None = None) -> datetime:
    """Normalize one captured reference instant to the local timezone."""
    value = reference or datetime.now().astimezone()
    if value.tzinfo is None:
        return value.replace(tzinfo=local_timezone())
    return value.astimezone(local_timezone())


def normalize_stored_datetime(value: Any) -> datetime:
    """Read legacy naive or current aware storage into one aware convention."""
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value or "").strip()
        if not text:
            raise ReminderTimeError("Reminder time is empty.")
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ReminderTimeError("Reminder time is not valid ISO-8601.") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=local_timezone())
    return parsed.astimezone(local_timezone())


def _parse_clock(value: str) -> time_type:
    normalized = value.strip().lower().replace(".", "")
    if normalized in {"midnight", "12 midnight"}:
        return time_type(0, 0)
    if normalized in {"noon", "12 noon"}:
        return time_type(12, 0)
    match = _CLOCK_RE.fullmatch(normalized)
    if not match:
        raise ReminderTimeError("Clock time is invalid or ambiguous.")
    hour = int(match.group("hour"))
    minute = int(match.group("minute") or 0)
    ampm = match.group("ampm")
    if minute > 59:
        raise ReminderTimeError("Clock minutes must be between 00 and 59.")
    if ampm:
        if hour < 1 or hour > 12:
            raise ReminderTimeError("12-hour clock hour is invalid.")
        if ampm == "pm" and hour != 12:
            hour += 12
        if ampm == "am" and hour == 12:
            hour = 0
    elif hour > 23:
        raise ReminderTimeError("24-hour clock hour is invalid.")
    return time_type(hour, minute)


def resolve_reminder_time(value: Any, now: datetime | None = None) -> datetime:
    """Resolve relative or absolute input to a future local aware datetime."""
    reference = local_now(now)
    if isinstance(value, datetime):
        target = normalize_stored_datetime(value)
    else:
        text = str(value or "").strip()
        if not text:
            raise ReminderTimeError("Reminder time is required.")

        relative = _RELATIVE_RE.fullmatch(text)
        if relative:
            amount = int(relative.group("amount"))
            unit = relative.group("unit").lower()
            if unit.startswith("sec"):
                target = reference + timedelta(seconds=amount)
            elif unit.startswith("min"):
                target = reference + timedelta(minutes=amount)
            else:
                target = reference + timedelta(hours=amount)
        else:
            try:
                target = normalize_stored_datetime(text)
            except ReminderTimeError:
                lowered = text.lower().strip()
                day = reference.date()
                clock_text = lowered
                if lowered.startswith("tomorrow"):
                    day += timedelta(days=1)
                    clock_text = lowered[len("tomorrow"):].strip()
                elif lowered.startswith("today"):
                    clock_text = lowered[len("today"):].strip()
                if clock_text.startswith("at "):
                    clock_text = clock_text[3:].strip()
                date_clock = _DATE_CLOCK_RE.fullmatch(lowered)
                if date_clock:
                    try:
                        day = date.fromisoformat(date_clock.group("day"))
                    except ValueError as exc:
                        raise ReminderTimeError("Reminder date is invalid.") from exc
                    clock_text = date_clock.group("clock")
                clock = _parse_clock(clock_text)
                target = datetime.combine(day, clock, tzinfo=reference.tzinfo)

    target = normalize_stored_datetime(target)
    if target <= reference:
        raise ReminderTimeError("That absolute reminder time has already passed.")
    return target
