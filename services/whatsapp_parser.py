import re
from datetime import datetime, timedelta


# * =========================================================
# * Scheduled WhatsApp Message Parser
# * =========================================================

def parse_scheduled_whatsapp(command):

    command = command.strip()

    now = datetime.now()

    # * =====================================================
    # * IN X SECONDS / MINUTES / HOURS
    #
    # * Examples:
    #
    # * send whatsapp to mom in 30 minutes saying I'm on the way
    # * send whatsapp to dad in 2 hours saying I will call
    # * send whatsapp to mom in 10 seconds saying hello
    # * =====================================================

    match = re.fullmatch(

        r"send\s+whatsapp\s+to\s+"
        r"(.+?)"
        r"\s+in\s+"
        r"(\d+)\s+"
        r"(seconds?|minutes?|hours?)"
        r"\s+saying\s+"
        r"(.+)",

        command,

        re.IGNORECASE,
    )

    if match:

        contact = match.group(1).strip()

        amount = int(
            match.group(2)
        )

        unit = match.group(3).lower()

        message = match.group(4).strip()

        if not contact or not message:
            return None

        if unit.startswith("second"):

            target = now + timedelta(
                seconds=amount
            )

        elif unit.startswith("minute"):

            target = now + timedelta(
                minutes=amount
            )

        else:

            target = now + timedelta(
                hours=amount
            )

        return {
            "contact": contact,
            "message": message,
            "send_at": target.isoformat(),
        }

    # * =====================================================
    # * TOMORROW AT TIME
    #
    # * Examples:
    #
    # * send whatsapp to dad tomorrow at 9 AM saying I'll call you
    # * send whatsapp to mom tomorrow at 10:30 PM saying good night
    # * =====================================================

    match = re.fullmatch(

        r"send\s+whatsapp\s+to\s+"
        r"(.+?)"
        r"\s+tomorrow\s+at\s+"
        r"(\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?))"
        r"\s+saying\s+"
        r"(.+)",

        command,

        re.IGNORECASE,
    )

    if match:

        contact = match.group(1).strip()

        time_text = match.group(2).strip()

        message = match.group(3).strip()

        if not contact or not message:
            return None

        time_text = (
            time_text
            .replace(".", "")
            .upper()
            .strip()
        )

        target = _parse_schedule_time(
            time_text,
            tomorrow=True,
        )

        if target is None:
            return None

        return {
            "contact": contact,
            "message": message,
            "send_at": target.isoformat(),
        }

    # * =====================================================
    # * TODAY AT TIME
    #
    # * Examples:
    #
    # * send whatsapp to mom today at 8 PM saying I'm home
    # * =====================================================

    match = re.fullmatch(

        r"send\s+whatsapp\s+to\s+"
        r"(.+?)"
        r"\s+today\s+at\s+"
        r"(\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?))"
        r"\s+saying\s+"
        r"(.+)",

        command,

        re.IGNORECASE,
    )

    if match:

        contact = match.group(1).strip()

        time_text = match.group(2).strip()

        message = match.group(3).strip()

        if not contact or not message:
            return None

        time_text = (
            time_text
            .replace(".", "")
            .upper()
            .strip()
        )

        target = _parse_schedule_time(
            time_text,
            tomorrow=False,
        )

        if target is None:
            return None

        return {
            "contact": contact,
            "message": message,
            "send_at": target.isoformat(),
        }

    return None


# * =========================================================
# * List Scheduled WhatsApp
# * =========================================================

def parse_list_scheduled_whatsapp(command):

    command = command.strip().lower()

    patterns = [
        r"list\s+(?:my\s+)?scheduled\s+whatsapp\s+messages?",
        r"show\s+(?:my\s+)?scheduled\s+whatsapp\s+messages?",
        r"list\s+(?:my\s+)?scheduled\s+messages?",
        r"show\s+(?:my\s+)?scheduled\s+messages?",
        r"what\s+(?:are|is)\s+(?:my\s+)?scheduled\s+whatsapp\s+messages?",
    ]

    for pattern in patterns:

        if re.fullmatch(
            pattern,
            command,
            re.IGNORECASE
        ):
            return True

    return False


# * =========================================================
# * Cancel Scheduled WhatsApp
# * =========================================================

def parse_cancel_scheduled_whatsapp(command):

    command = command.strip().lower()

    match = re.fullmatch(
        r"(?:cancel|delete|remove)\s+"
        r"(?:scheduled\s+)?"
        r"(?:whatsapp\s+)?"
        r"(?:message\s+)?"
        r"(?:number\s+)?"
        r"(\d+)",
        command,
        re.IGNORECASE,
    )

    if match:

        return int(
            match.group(1)
        )

    return None


# * =========================================================
# * Reschedule Scheduled WhatsApp
# * =========================================================

def parse_reschedule_scheduled_whatsapp(command):

    command = command.strip()

    # * -----------------------------------------------------
    # * Tomorrow at TIME
    # * -----------------------------------------------------

    match = re.fullmatch(
        r"reschedule\s+"
        r"(?:whatsapp\s+)?"
        r"(?:message\s+)?"
        r"(?:number\s+)?"
        r"(\d+)"
        r"\s+(?:to|for)\s+"
        r"tomorrow\s+at\s+"
        r"(\d{1,2}(?::\d{2})?\s*"
        r"(?:a\.?m\.?|p\.?m\.?))",
        command,
        re.IGNORECASE,
    )

    if match:

        reminder_id = int(
            match.group(1)
        )

        time_text = (
            match.group(2)
            .replace(".", "")
            .upper()
            .strip()
        )

        send_at = _parse_whatsapp_clock_time(
            time_text,
            tomorrow=True,
        )

        if send_at:

            return {
                "id": reminder_id,
                "send_at": send_at.isoformat(),
            }

        return None

    # * -----------------------------------------------------
    # * Today / next occurrence at TIME
    # * -----------------------------------------------------

    match = re.fullmatch(
        r"reschedule\s+"
        r"(?:whatsapp\s+)?"
        r"(?:message\s+)?"
        r"(?:number\s+)?"
        r"(\d+)"
        r"\s+(?:to|for)\s+"
        r"(\d{1,2}(?::\d{2})?\s*"
        r"(?:a\.?m\.?|p\.?m\.?))",
        command,
        re.IGNORECASE,
    )

    if match:

        reminder_id = int(
            match.group(1)
        )

        time_text = (
            match.group(2)
            .replace(".", "")
            .upper()
            .strip()
        )

        send_at = _parse_whatsapp_clock_time(
            time_text
        )

        if send_at:

            return {
                "id": reminder_id,
                "send_at": send_at.isoformat(),
            }

    # * -----------------------------------------------------
    # * In X minutes
    # * -----------------------------------------------------

    match = re.fullmatch(
        r"reschedule\s+"
        r"(?:whatsapp\s+)?"
        r"(?:message\s+)?"
        r"(?:number\s+)?"
        r"(\d+)"
        r"\s+(?:to|for)\s+"
        r"in\s+"
        r"(\d+)\s+"
        r"(second|seconds|minute|minutes|hour|hours)",
        command,
        re.IGNORECASE,
    )

    if match:

        reminder_id = int(
            match.group(1)
        )

        amount = int(
            match.group(2)
        )

        unit = match.group(3).lower()

        now = datetime.now()

        if unit.startswith("second"):

            target = now + timedelta(
                seconds=amount
            )

        elif unit.startswith("minute"):

            target = now + timedelta(
                minutes=amount
            )

        else:

            target = now + timedelta(
                hours=amount
            )

        return {
            "id": reminder_id,
            "send_at": target.isoformat(),
        }

    return None


# * =========================================================
# * Clock Helper
# * =========================================================

def _parse_whatsapp_clock_time(
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

        parsed = None

        for fmt in (
            "%I:%M %p",
            "%I %p",
        ):

            try:

                parsed = datetime.strptime(
                    value,
                    fmt,
                )

                break

            except ValueError:
                continue

        if parsed is None:
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
            f"[WHATSAPP PARSER ERROR] {e}"
        )

        return None

# * =========================================================
# * Schedule Clock Parser
# * =========================================================

def _parse_schedule_time(
    value,
    tomorrow=False,
):

    try:

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

            # * "today at 8 PM" when 8 PM already passed
            # * should not accidentally schedule yesterday.
            return None

        return target

    except Exception as e:

        print(
            f"[WHATSAPP SCHEDULE PARSER ERROR] {e}"
        )

        return None


# * =========================================================
# * Normal WhatsApp Message Parser
# * =========================================================

def parse_whatsapp(command):

    command = command.strip()

    patterns = [

        # * send whatsapp to John saying hello
        (
            r"send\s+whatsapp\s+to\s+(.+?)"
            r"\s+saying\s+(.+)"
        ),

        # * send whatsapp message to John saying hello
        (
            r"send\s+whatsapp\s+message\s+to\s+(.+?)"
            r"\s+saying\s+(.+)"
        ),

        # * send message to John saying hello
        (
            r"send\s+message\s+to\s+(.+?)"
            r"\s+saying\s+(.+)"
        ),

        # * send whatsapp message to John hello
        (
            r"send\s+whatsapp\s+message\s+to\s+(.+?)"
            r"\s+(.+)"
        ),

        # * send message to John hello
        (
            r"send\s+message\s+to\s+(.+?)"
            r"\s+(.+)"
        ),

        # * send whatsapp to John hello
        (
            r"send\s+whatsapp\s+to\s+(.+?)"
            r"\s+(.+)"
        ),
    ]

    for pattern in patterns:

        match = re.fullmatch(
            pattern,
            command,
            re.IGNORECASE,
        )

        if match:

            contact = match.group(1).strip()

            message = match.group(2).strip()

            if contact and message:

                return {
                    "contact": contact,
                    "message": message,
                }

    return None

# * =========================================================
# * WhatsApp Call Parser
# * =========================================================

def parse_whatsapp_call(command):

    command = command.strip()

    patterns = [

        # * call dad on whatsapp
        r"call\s+(.+?)\s+on\s+whatsapp",

        # * whatsapp call dad
        r"whatsapp\s+call\s+(.+)",

        # * call dad via whatsapp
        r"call\s+(.+?)\s+via\s+whatsapp",

        # * make a whatsapp call to dad
        r"make\s+(?:a\s+)?whatsapp\s+call\s+to\s+(.+)",

    ]

    for pattern in patterns:

        match = re.fullmatch(
            pattern,
            command,
            re.IGNORECASE,
        )

        if match:

            contact = match.group(1).strip()

            if contact:

                return {
                    "contact": contact
                }

    return None


# * =========================================================
# * WhatsApp Video Call Parser
# * =========================================================

def parse_whatsapp_video_call(command):

    command = command.strip()

    patterns = [

        # * video call dad on whatsapp
        r"video\s+call\s+(.+?)\s+on\s+whatsapp",

        # * whatsapp video call dad
        r"whatsapp\s+video\s+call\s+(.+)",

        # * video call dad via whatsapp
        r"video\s+call\s+(.+?)\s+via\s+whatsapp",

        # * make a whatsapp video call to dad
        r"make\s+(?:a\s+)?whatsapp\s+video\s+call\s+to\s+(.+)",

    ]

    for pattern in patterns:

        match = re.fullmatch(
            pattern,
            command,
            re.IGNORECASE,
        )

        if match:

            contact = match.group(1).strip()

            if contact:

                return {
                    "contact": contact
                }

    return None