import re
from datetime import datetime, timedelta


# * =========================================================
# * MEMORY ROUTER
# * Notes + Reminders
#
# ! IMPORTANT:
# ! This router must NOT call AI.
# * =========================================================

def memory_route(command):

    command = command.lower().strip()

    # * =====================================================
    # * NOTES
    # * =====================================================

    # * -----------------------------------------------------
    # * Create note
    #
    # * make a note to buy milk
    # * make note to buy milk
    # * take a note to buy milk
    # * take note buy milk
    # * note buy milk
    # * note I have to buy milk
    # * write a note about project
    # * save a note saying call John
    # * -----------------------------------------------------

    note_match = re.match(
        r"^(?:"
        r"make\s+(?:a\s+)?note"
        r"|take\s+(?:a\s+)?note"
        r"|write\s+(?:a\s+)?note"
        r"|save\s+(?:a\s+)?note"
        r"|create\s+(?:a\s+)?note"
        r"|add\s+(?:a\s+)?note"
        r"|note"
        r")"
        r"(?:\s+(?:to|that|about|for|saying))?"
        r"\s+(.+)$",
        command,
        re.IGNORECASE,
    )

    if note_match:

        text = note_match.group(1).strip()

        if text:

            print(
                f"[MEMORY ROUTER] Creating note: {text}"
            )

            return [
                {
                    "action": "create_note",
                    "text": text,
                }
            ]

    # * -----------------------------------------------------
    # * List notes
    # * -----------------------------------------------------

    if command in (
        "list notes",
        "list my notes",
        "show notes",
        "show my notes",
        "read notes",
        "read my notes",
        "what are my notes",
        "whats my notes",
        "what's my notes",
        "display notes",
    ):

        print(
            "[MEMORY ROUTER] Listing notes"
        )

        return [
            {
                "action": "list_notes"
            }
        ]

    # * -----------------------------------------------------
    # * Clear notes
    # * -----------------------------------------------------

    if command in (
        "clear notes",
        "clear my notes",
        "delete notes",
        "delete my notes",
        "remove notes",
        "remove my notes",
    ):

        print(
            "[MEMORY ROUTER] Clearing notes"
        )

        return [
            {
                "action": "clear_notes"
            }
        ]

    # * =====================================================
    # * REMINDERS
    # * =====================================================

    # * -----------------------------------------------------
    # * Remind me in X seconds/minutes/hours
    #
    # * remind me in 30 seconds to check
    # * remind me in 5 minutes to call John
    # * remind me in 2 hours to check the oven
    # * -----------------------------------------------------

    match = re.match(
        r"^remind\s+me\s+in\s+"
        r"(\d+)\s+"
        r"(second|seconds|sec|secs|"
        r"minute|minutes|min|mins|"
        r"hour|hours|hr|hrs)"
        r"(?:\s+to)?\s+(.+)$",
        command,
        re.IGNORECASE,
    )

    if match:

        amount = int(match.group(1))
        unit = match.group(2).lower()
        text = match.group(3).strip()

        if not text:
            return None

        if unit.startswith("sec"):

            target = (
                datetime.now()
                + timedelta(seconds=amount)
            )

        elif unit.startswith("min"):

            target = (
                datetime.now()
                + timedelta(minutes=amount)
            )

        else:

            target = (
                datetime.now()
                + timedelta(hours=amount)
            )

        remind_at = target.isoformat()

        print(
            "[MEMORY ROUTER] Creating reminder:",
            text,
            "->",
            remind_at,
        )

        return [
            {
                "action": "create_reminder",
                "text": text,
                "remind_at": remind_at,
            }
        ]

    # * -----------------------------------------------------
    # * Remind me at TIME
    #
    # * remind me at 10:30 PM to call John
    # * remind me at 10:30 p.m. to call John
    # * remind me at 10 PM to call John
    # * remind me at 8 AM to take medicine
    # * -----------------------------------------------------

    match = re.match(
        r"^remind\s+me\s+at\s+"
        r"(\d{1,2}(?::\d{2})?\s*"
        r"(?:a\.?m\.?|p\.?m\.?))"
        r"\s+(?:to\s+)?(.+)$",
        command,
        re.IGNORECASE,
    )

    if match:

        time_text = match.group(1).strip()
        text = match.group(2).strip()

        time_text = (
            time_text
            .replace(".", "")
            .upper()
        )

        target = _parse_clock_time(
            time_text
        )

        if target and text:

            remind_at = target.isoformat()

            print(
                "[MEMORY ROUTER] Creating reminder:",
                text,
                "->",
                remind_at,
            )

            return [
                {
                    "action": "create_reminder",
                    "text": text,
                    "remind_at": remind_at,
                }
            ]

    # * -----------------------------------------------------
    # * Remind me tomorrow at TIME
    #
    # * remind me tomorrow at 10 PM to call John
    # * -----------------------------------------------------

    match = re.match(
        r"^remind\s+me\s+tomorrow\s+at\s+"
        r"(\d{1,2}(?::\d{2})?\s*"
        r"(?:a\.?m\.?|p\.?m\.?))"
        r"\s+(?:to\s+)?(.+)$",
        command,
        re.IGNORECASE,
    )

    if match:

        time_text = match.group(1).strip()
        text = match.group(2).strip()

        time_text = (
            time_text
            .replace(".", "")
            .upper()
        )

        target = _parse_clock_time(
            time_text,
            tomorrow=True,
        )

        if target and text:

            remind_at = target.isoformat()

            print(
                "[MEMORY ROUTER] Creating reminder:",
                text,
                "->",
                remind_at,
            )

            return [
                {
                    "action": "create_reminder",
                    "text": text,
                    "remind_at": remind_at,
                }
            ]

    # * -----------------------------------------------------
    # * List reminders
    # * -----------------------------------------------------

    if command in (
        "list reminders",
        "list my reminders",
        "show reminders",
        "show my reminders",
        "read reminders",
        "read my reminders",
        "what are my reminders",
        "display reminders",
    ):

        print(
            "[MEMORY ROUTER] Listing reminders"
        )

        return [
            {
                "action": "list_reminders"
            }
        ]

    # * -----------------------------------------------------
    # * Cancel reminder
    #
    # * cancel reminder 3
    # * cancel reminder number 3
    # * -----------------------------------------------------

    match = re.match(
        r"^cancel\s+(?:reminder\s+)?"
        r"(?:number\s+)?(\d+)$",
        command,
        re.IGNORECASE,
    )

    if match:

        reminder_id = int(
            match.group(1)
        )

        print(
            "[MEMORY ROUTER] Cancelling reminder:",
            reminder_id,
        )

        return [
            {
                "action": "cancel_reminder",
                "id": reminder_id,
            }
        ]

    return None


# * =========================================================
# * CLOCK PARSER
# * =========================================================

def _parse_clock_time(
    value,
    tomorrow=False,
):

    try:

        value = (
            value
            .replace(".", "")
            .upper()
            .strip()
        )

        formats = (
            "%I:%M %p",
            "%I %p",
        )

        parsed = None

        for fmt in formats:

            try:

                parsed = datetime.strptime(
                    value,
                    fmt,
                )

                break

            except ValueError:
                continue

        if parsed is None:

            print(
                f"[MEMORY ROUTER] Invalid time: {value}"
            )

            return None

        now = datetime.now()

        target = now.replace(
            hour=parsed.hour,
            minute=parsed.minute,
            second=0,
            microsecond=0,
        )

        if tomorrow:

            target += timedelta(
                days=1
            )

        elif target <= now:

            target += timedelta(
                days=1
            )

        return target

    except Exception as e:

        print(
            f"[MEMORY ROUTER ERROR] {e}"
        )

        return None