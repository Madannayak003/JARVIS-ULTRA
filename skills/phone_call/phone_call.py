"""Phone-call commands for a connected Android device.

Explicit call commands use Android's documented ``ACTION_CALL`` intent. If
the device rejects that intent, the skill falls back to a prepared dialer and
clearly asks the user to press Call. It never injects touch/keyboard input or
claims that a call is active before telephony state confirms it.
"""

from __future__ import annotations

import re
import unicodedata

from core.registry import register
from services.android import get_android_manager
from services.android.android_intents import ACTION_CALL, ACTION_DIAL
from services.android.models import IntentSpec


_PHONE_NUMBER_RE = re.compile(r"^\+?[0-9]{7,15}$")

_RELATIONSHIP_ALIASES = {
    "mom": ("mom", "mother", "mummy", "amma"),
    "dad": ("dad", "father", "daddy", "appa"),
    "brother": ("brother", "anna", "bhai"),
    "sister": ("sister", "akka", "behen"),
}


def _say(message: str) -> None:
    print(f"[PHONE CALL] {message}")
    try:
        from voice.manager import speak

        speak(message)
    except Exception:
        pass


def normalize_phone_number(value: str) -> str | None:
    """Return a conservative E.164-like value, or ``None`` if invalid."""
    candidate = str(value or "").strip()
    candidate = re.sub(r"[\s().-]", "", candidate)
    if candidate.startswith("00"):
        candidate = "+" + candidate[2:]
    if not _PHONE_NUMBER_RE.fullmatch(candidate):
        return None
    return candidate


def _normalize_contact_name(value: str) -> str:
    value = unicodedata.normalize("NFKC", str(value or ""))
    value = value.casefold().strip()
    value = re.sub(r"[^\w]+", " ", value, flags=re.UNICODE)
    return " ".join(value.split())


def _phone_digits(value: str) -> str:
    return re.sub(r"\D", "", str(value or ""))


def _numbers_match(left: str, right: str) -> bool:
    left_digits = _phone_digits(left)
    right_digits = _phone_digits(right)
    if not left_digits or not right_digits:
        return False
    return left_digits == right_digits or (
        len(left_digits) >= 10
        and len(right_digits) >= 10
        and left_digits[-10:] == right_digits[-10:]
    )


def _spoken_contact_name(value: str) -> str:
    """Keep speech natural when a display name contains symbols or emoji."""
    cleaned = re.sub(r"[^\w\s+.-]", " ", str(value or ""), flags=re.UNICODE)
    cleaned = " ".join(cleaned.split())
    if cleaned.isupper():
        return cleaned.title()
    return cleaned


def _parse_phone_contacts(output: str) -> list[dict[str, str]]:
    """Parse the read-only Android phone-data provider output.

    Samsung's provider accepts the full-row query but rejects multi-column
    projection syntax under the shell content command. The parser therefore
    extracts only ``display_name`` and ``data1`` from each returned row.
    """
    contacts: list[dict[str, str]] = []
    for row in re.split(r"\bRow:\s*\d+\s*", output or "")[1:]:
        fields = {
            field: _provider_field(row, field)
            for field in ("display_name", "data1", "data4", "contact_id")
        }
        name = fields["display_name"]
        number = fields["data1"]
        if name and number and name.casefold() != "null" and number.casefold() != "null":
            contacts.append(
                {
                    "name": name,
                    "number": number,
                    "normalized_number": fields["data4"],
                    "contact_id": fields["contact_id"],
                }
            )
    return contacts


def _provider_field(row: str, field: str) -> str:
    """Read a provider field without depending on Samsung column order."""
    match = re.search(
        rf"(?:^|,\s*){re.escape(field)}=(.*?)(?=,\s*[A-Za-z_][A-Za-z0-9_]*=|$)",
        row,
        re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def query_phone_contacts() -> list[dict[str, str]] | None:
    """Read phone contacts only when the connected device permits it."""
    manager = get_android_manager()
    try:
        result = manager.run_adb(
            [
                "shell",
                "content",
                "query",
                "--uri",
                "content://com.android.contacts/data/phones",
            ]
        )
    except Exception:
        return None
    if not result.ok:
        return None
    return _parse_phone_contacts(result.stdout)


def _find_contact(name: str) -> list[dict[str, str]] | None:
    contacts = query_phone_contacts()
    if contacts is None:
        return None
    target = _normalize_contact_name(name)
    if not target:
        return []

    exact = [
        contact
        for contact in contacts
        if _normalize_contact_name(contact.get("name", "")) == target
    ]
    if exact:
        return exact

    query_tokens = set(target.split())
    matches = []
    for contact in contacts:
        contact_tokens = set(_normalize_contact_name(contact.get("name", "")).split())
        if query_tokens and query_tokens.issubset(contact_tokens):
            matches.append(contact)
    if matches:
        return matches

    # * Relationship aliases are evaluated in deterministic priority order.
    # * For example, "mom" prefers a unique contact containing "mother" over
    # * unrelated contacts containing the later fallback alias "amma".
    for alias in _RELATIONSHIP_ALIASES.get(target, ()):
        alias_tokens = set(_normalize_contact_name(alias).split())
        alias_matches = [
            contact
            for contact in contacts
            if alias_tokens
            and alias_tokens.issubset(
                set(_normalize_contact_name(contact.get("name", "")).split())
            )
        ]
        if alias_matches:
            return alias_matches
    return []


def _start_call(number: str, display_name: str = "") -> bool:
    manager = get_android_manager()
    try:
        started = manager.launch_intent(
            IntentSpec(action=ACTION_CALL, data=f"tel:{number}")
        )
    except Exception as error:
        print(f"[PHONE CALL] Call launch failed: {error}")
        started = False

    if started:
        caller = _spoken_contact_name(display_name) or number
        _say(f"Calling {caller}.")
        try:
            from .monitor import get_call_monitor

            get_call_monitor().begin_outgoing(number, display_name)
        except Exception as error:
            print(f"[PHONE CALL] Outgoing state update skipped: {error}")
        return True

    # ! A permission/security policy may reject ACTION_CALL. Keep the fallback
    # ! safe and explicit: prepare the dialer, never simulate pressing Call.
    try:
        opened = manager.launch_intent(
            IntentSpec(action=ACTION_DIAL, data=f"tel:{number}")
        )
    except Exception as error:
        print(f"[PHONE CALL] Dialer fallback failed: {error}")
        opened = False
    if opened:
        _say("The dialer is ready. Please press Call.")
    else:
        _say("I couldn't start the call.")
    return opened


def phone_call_number(data=None):
    data = data or {}
    number = normalize_phone_number(data.get("phone_number", ""))
    if not number:
        _say("That does not look like a valid phone number.")
        return False
    return _start_call(number)


def phone_call_contact(data=None):
    data = data or {}
    name = str(data.get("contact_name", "")).strip()
    if not name:
        _say("Please tell me which contact to call.")
        return False

    matches = _find_contact(name)
    if matches is None:
        _say("I could not safely read contacts from the connected phone.")
        return False
    if not matches:
        _say(f"I couldn't find {name} in your phone contacts.")
        return False
    if len(matches) > 1:
        _say(f"I found {len(matches)} contacts named {name}. Which one should I call?")
        return False

    contact = matches[0]
    number = normalize_phone_number(contact.get("number", ""))
    if not number:
        _say(f"I found {name}, but the saved phone number is not valid.")
        return False

    return _start_call(number, contact.get("name", name))


def phone_call_confirmed(data=None):
    data = data or {}
    number = normalize_phone_number(data.get("phone_number", ""))
    if not number:
        _say("The contact phone number is no longer available.")
        return False
    return _start_call(number, data.get("caller_name", ""))


def call_status(data=None):
    try:
        from .monitor import get_call_monitor

        message = get_call_monitor().status_message()
    except Exception:
        message = "No active call."
    _say(message)
    return True


def _recent_missed_calls() -> list[dict[str, str]] | None:
    manager = get_android_manager()
    result = manager.run_adb(
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
        ]
    )
    if not result.ok:
        return None
    calls: list[dict[str, str]] = []
    for row in re.split(r"\bRow:\s*\d+\s*", result.stdout or "")[1:]:
        number_match = re.search(r"\bnumber=(.*?),\s*date=", row, re.DOTALL)
        date_match = re.search(r"\bdate=(\d+)", row)
        number = number_match.group(1).strip() if number_match else ""
        date = date_match.group(1) if date_match else ""
        if number:
            calls.append({"number": number, "date": date})
    return calls


def missed_calls(data=None):
    try:
        calls = _recent_missed_calls()
    except Exception:
        calls = None
    if calls is None:
        _say("I could not safely read the phone call log.")
        return False
    if not calls:
        _say("You have no recent missed calls.")
        return True

    contacts = query_phone_contacts() or []
    summaries = []
    for call in calls[:5]:
        name = next(
            (
                contact.get("name", "").strip()
                for contact in contacts
                if _numbers_match(contact.get("number", ""), call["number"])
                and contact.get("name", "").strip()
            ),
            "",
        )
        summaries.append(name or call["number"] or "an unknown number")
    _say("Missed calls from " + ", ".join(summaries) + ".")
    return True


def _manual_call_control(action: str) -> bool:
    messages = {
        "answer": "Answering calls through ADB is not safely available on this Android device. Please answer the call manually.",
        "reject": "Rejecting calls through ADB is not safely available on this Android device. Please reject the call manually.",
        "end": "Ending calls through ADB is not safely available on this Android device. Please end the call manually.",
    }
    _say(messages[action])
    return False


def answer_call(data=None):
    return _manual_call_control("answer")


def reject_call(data=None):
    return _manual_call_control("reject")


def end_call(data=None):
    return _manual_call_control("end")


register("phone_call_number", phone_call_number, category="phone_calls")
register("phone_call_contact", phone_call_contact, category="phone_calls")
register("phone_call_confirmed", phone_call_confirmed, category="phone_calls")
register("answer_call", answer_call, category="phone_calls")
register("reject_call", reject_call, category="phone_calls")
register("end_call", end_call, category="phone_calls")
register("call_status", call_status, category="phone_calls")
register("missed_calls", missed_calls, category="phone_calls")
