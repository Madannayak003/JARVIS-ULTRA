import json
import threading
import time
from pathlib import Path
from datetime import datetime

from core.registry import register
from voice.manager import speak

from services.whatsapp_api import (
    open_whatsapp,
    close_whatsapp,
    send_message,
    send_photo,
    send_file,
    call_contact,
    video_call_contact,
)

from services.file_manager import (latest_photo,latest_screenshot,find_file)

from services.contact_manager import (resolve_contact)

from core.file_selection_memory import (
    set_files,
    get_files,
    clear_files,
)

from core.whatsapp_memory import (
    set_contact,
    get_contact,
    clear_contact,
    set_pending_message,
    get_pending_message,
    clear_pending_message
)

# * =========================================================
# * Scheduled WhatsApp Storage
# * =========================================================

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

SCHEDULED_WHATSAPP_FILE = (
    DATA_DIR / "whatsapp_scheduled.json"
)

def whatsapp_open(data):

    if open_whatsapp():

        speak("Opening WhatsApp.")

    else:

        speak("Unable to open WhatsApp.")

    return True


def whatsapp_close(data):

    close_whatsapp()

    speak("Closing WhatsApp.")

    return True

def whatsapp_send_message(data):

    contact = resolve_contact(
    data.get("contact", "").strip()
    )
    message = data.get("message", "").strip()

    if not contact:

        set_pending_message(message)

        speak("Which contact should I send it to?")

        return True

    if not message:

        speak("What should I send?")

        return True

    speak(f"Sending your message to {contact}.")

    ok = send_message(contact, message)

    if ok:

        speak("Message sent.")

    else:

        speak("I couldn't send the message.")

    return True

# * =========================================================
# * Scheduled WhatsApp Storage Helpers
# * =========================================================

def _load_scheduled_whatsapp():

    if not SCHEDULED_WHATSAPP_FILE.exists():

        return []

    try:

        with open(
            SCHEDULED_WHATSAPP_FILE,
            "r",
            encoding="utf-8",
        ) as f:

            data = json.load(f)

        if isinstance(data, list):

            return data

    except Exception as e:

        print(
            f"[WHATSAPP SCHEDULER ERROR] "
            f"Load failed: {e}"
        )

    return []


def _save_scheduled_whatsapp(messages):

    try:

        with open(
            SCHEDULED_WHATSAPP_FILE,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                messages,
                f,
                indent=4,
                ensure_ascii=False,
            )

        return True

    except Exception as e:

        print(
            f"[WHATSAPP SCHEDULER ERROR] "
            f"Save failed: {e}"
        )

        return False
    
# * =========================================================
# * Schedule WhatsApp Message
# * =========================================================

def schedule_whatsapp_message(data=None):

    data = data or {}

    contact = str(
        data.get("contact", "")
    ).strip()

    message = str(
        data.get("message", "")
    ).strip()

    send_at = str(
        data.get("send_at", "")
    ).strip()

    if not contact:

        speak(
            "Which contact should I send it to?"
        )

        return False

    if not message:

        speak(
            "What message should I schedule?"
        )

        return False

    if not send_at:

        speak(
            "When should I send the message?"
        )

        return False

    # * -----------------------------------------------------
    # * Validate datetime
    # * -----------------------------------------------------

    try:

        target = datetime.fromisoformat(
            send_at
        )

    except Exception:

        print(
            "[WHATSAPP SCHEDULER] "
            f"Invalid datetime: {send_at}"
        )

        speak(
            "I couldn't understand the scheduled time."
        )

        return False

    # * -----------------------------------------------------
    # * Load existing messages
    # * -----------------------------------------------------

    messages = _load_scheduled_whatsapp()

    # * -----------------------------------------------------
    # * Generate ID
    # * -----------------------------------------------------

    if messages:

        message_id = max(
            int(item.get("id", 0))
            for item in messages
        ) + 1

    else:

        message_id = 1

    # * -----------------------------------------------------
    # * Create scheduled message
    # * -----------------------------------------------------

    scheduled = {

        "id": message_id,

        "contact": contact,

        "message": message,

        "send_at": target.isoformat(),

        "completed": False,

        "created_at": datetime.now().isoformat(),
    }

    messages.append(
        scheduled
    )

    # * -----------------------------------------------------
    # * Save
    # * -----------------------------------------------------

    if not _save_scheduled_whatsapp(
        messages
    ):

        speak(
            "I couldn't save the scheduled WhatsApp message."
        )

        return False

    print(
        "[WHATSAPP SCHEDULER] Saved:",
        scheduled
    )

    # * -----------------------------------------------------
    # * Voice confirmation
    # * -----------------------------------------------------

    formatted_time = target.strftime(
        "%I:%M %p"
    ).lstrip("0")

    speak(
        f"I'll send your WhatsApp message "
        f"to {contact} at {formatted_time}."
    )

    return True

# * =========================================================
# * Scheduled WhatsApp Worker
# * =========================================================

_scheduler_started = False
_scheduler_lock = threading.Lock()

def list_scheduled_whatsapp(data=None):

    messages = _load_scheduled_whatsapp()

    active = [
        item
        for item in messages
        if not item.get("completed", False)
    ]

    if not active:

        speak(
            "You don't have any scheduled WhatsApp messages."
        )

        return True

    print("\n[WHATSAPP SCHEDULED]")

    for item in active:

        try:

            target = datetime.fromisoformat(
                item["send_at"]
            )

            formatted = target.strftime(
                "%d %B at %I:%M %p"
            ).lstrip("0")

        except Exception:

            formatted = item.get(
                "send_at",
                "unknown time"
            )

        print(
            f"#{item.get('id')} "
            f"{item.get('contact')} "
            f"-> {item.get('message')} "
            f"at {formatted}"
        )

    speak(
        f"You have {len(active)} scheduled WhatsApp messages."
    )

    return True


def get_scheduled_whatsapp_items():
    """Read-only data access for the existing Schedule Center."""
    return _load_scheduled_whatsapp()

def cancel_scheduled_whatsapp(data=None):

    data = data or {}

    try:

        message_id = int(
            data.get("id")
        )

    except Exception:

        speak(
            "I need the scheduled message number."
        )

        return False

    messages = _load_scheduled_whatsapp()

    found = None

    for item in messages:

        if int(
            item.get("id", -1)
        ) == message_id:

            found = item
            break

    if found is None:

        speak(
            f"I couldn't find scheduled message {message_id}."
        )

        return False

    if found.get("completed", False):

        speak(
            "That message has already been sent."
        )

        return False

    found["completed"] = True

    found["cancelled"] = True

    found["cancelled_at"] = (
        datetime.now().isoformat()
    )

    if not _save_scheduled_whatsapp(messages):

        speak(
            "I couldn't cancel that scheduled message."
        )

        return False

    print(
        f"[WHATSAPP SCHEDULER] "
        f"Cancelled #{message_id}"
    )

    speak(
        f"Scheduled WhatsApp message {message_id} cancelled."
    )

    return True


def reschedule_scheduled_whatsapp(data=None):

    data = data or {}

    try:

        message_id = int(
            data.get("id")
        )

    except Exception:

        speak(
            "I need the scheduled message number."
        )

        return False

    send_at = str(
        data.get("send_at", "")
    ).strip()

    if not send_at:

        speak(
            "I need the new time."
        )

        return False

    try:

        target = datetime.fromisoformat(
            send_at
        )

    except Exception:

        speak(
            "I couldn't understand the new time."
        )

        return False

    if target <= datetime.now():

        speak(
            "That time has already passed."
        )

        return False

    messages = _load_scheduled_whatsapp()

    found = None

    for item in messages:

        if int(
            item.get("id", -1)
        ) == message_id:

            found = item
            break

    if found is None:

        speak(
            f"I couldn't find scheduled message {message_id}."
        )

        return False

    if found.get("completed", False):

        speak(
            "That message has already been completed."
        )

        return False

    found["send_at"] = target.isoformat()

    found["rescheduled_at"] = (
        datetime.now().isoformat()
    )

    if not _save_scheduled_whatsapp(messages):

        speak(
            "I couldn't reschedule that message."
        )

        return False

    print(
        f"[WHATSAPP SCHEDULER] "
        f"Rescheduled #{message_id} -> "
        f"{target.isoformat()}"
    )

    speak(
        "Scheduled WhatsApp message "
        f"{message_id} moved to "
        f"{target.strftime('%I:%M %p').lstrip('0')}."
    )

    return True


def _whatsapp_scheduler_worker():

    print(
        "[WHATSAPP SCHEDULER] Background scheduler started"
    )

    while True:

        try:

            messages = _load_scheduled_whatsapp()

            now = datetime.now()

            changed = False

            for item in messages:

                # * -----------------------------------------
                # * Already sent
                # * -----------------------------------------

                if item.get("completed", False):
                    continue

                send_at = item.get("send_at")

                if not send_at:
                    continue

                # * -----------------------------------------
                # * Parse scheduled time
                # * -----------------------------------------

                try:

                    target = datetime.fromisoformat(
                        send_at
                    )

                except Exception as e:

                    print(
                        "[WHATSAPP SCHEDULER] "
                        f"Invalid time for #{item.get('id')}: {e}"
                    )

                    continue

                # * -----------------------------------------
                # * Not time yet
                # * -----------------------------------------

                if target > now:
                    continue

                # * -----------------------------------------
                # * Resolve saved contact
                # * -----------------------------------------

                alias = str(
                    item.get("contact", "")
                ).strip()

                contact = resolve_contact(alias)

                message = str(
                    item.get("message", "")
                ).strip()

                if not contact or not message:

                    print(
                        "[WHATSAPP SCHEDULER] "
                        f"Invalid message #{item.get('id')}"
                    )

                    continue

                print(
                    "[WHATSAPP SCHEDULER] Sending:",
                    f"#{item.get('id')}",
                    f"{alias} -> {contact}",
                    message,
                )

                # * -----------------------------------------
                # * Send
                # * -----------------------------------------

                try:

                    ok = send_message(
                        contact,
                        message
                    )

                except Exception as e:

                    print(
                        "[WHATSAPP SCHEDULER] "
                        f"Send failed for #{item.get('id')}: {e}"
                    )

                    ok = False

                # * -----------------------------------------
                # * SUCCESS
                # * -----------------------------------------

                if ok:

                    item["completed"] = True

                    item["sent_at"] = (
                        datetime.now().isoformat()
                    )

                    item["resolved_contact"] = contact

                    changed = True

                    print(
                        "[WHATSAPP SCHEDULER] "
                        f"Sent successfully: #{item.get('id')}"
                    )

                    speak(
                        f"Scheduled WhatsApp message sent to {contact}."
                    )

                # * -----------------------------------------
                # * FAILURE
                # * -----------------------------------------

                else:

                    print(
                        "[WHATSAPP SCHEDULER] "
                        f"Message #{item.get('id')} "
                        "was not sent. Keeping pending."
                    )

            # * ---------------------------------------------
            # * Save changes
            # * ---------------------------------------------

            if changed:

                _save_scheduled_whatsapp(
                    messages
                )

        except Exception as e:

            print(
                "[WHATSAPP SCHEDULER ERROR]",
                e
            )

        time.sleep(1)


# * =========================================================
# * Start Scheduler
# * =========================================================

def _start_whatsapp_scheduler():

    global _scheduler_started

    with _scheduler_lock:

        if _scheduler_started:
            return

        thread = threading.Thread(
            target=_whatsapp_scheduler_worker,
            daemon=True,
            name="WhatsAppScheduler",
        )

        thread.start()

        _scheduler_started = True

        print(
            "[WHATSAPP SCHEDULER] Scheduler initialized"
        )

def whatsapp_send_latest_photo(data):

    contact = resolve_contact(
        data.get("contact", "").strip()
    )

    photo = latest_photo()

    if not photo:

        speak("I couldn't find any recent photo.")

        return True

    speak(f"Sending the latest photo to {contact}.")

    ok = send_photo(
        contact,
        str(photo)
    )

    if ok:

        speak("Photo sent.")

    else:

        speak("I couldn't send the photo.")

    return True

def whatsapp_send_latest_screenshot(data):

    contact = resolve_contact(
        data.get("contact", "").strip()
    )

    image = latest_screenshot()

    if not image:

        speak("I couldn't find any screenshot.")

        return True

    speak(f"Sending the latest screenshot to {contact}.")

    ok = send_photo(
        contact,
        str(image)
    )

    if ok:

        speak("Screenshot sent.")

    else:

        speak("I couldn't send the screenshot.")

    return True

def whatsapp_send_file(data):

    contact = resolve_contact(
        data.get("contact", "").strip()
    )

    filename = data.get("filename", "").strip()

    matches = find_file(filename)

    if not matches:

        speak(f"I couldn't find {filename}.")

        return True

    # * Only one file
    if len(matches) == 1:

        file = matches[0]

        speak(f"Sending {file.name} to {contact}.")

        ok = send_file(
            contact,
            str(file)
        )

        if ok:

            speak("File sent.")

        else:

            speak("I couldn't send the file.")

        return True

    # * Multiple files

    set_files({

        "contact": contact,

        "files": matches

    })

    speak(f"I found {len(matches)} matching files.")

    for i, file in enumerate(matches[:5], 1):

        speak(f"{i}. {file.name}")

    speak("Which one should I send?")

    return True

def whatsapp_send_selected_file(data):

    pending = get_files()

    if not pending:

        speak("There isn't any pending file selection.")

        return True

    files = pending["files"]
    contact = pending["contact"]

    index = data["index"]

    if index >= len(files):

        speak("That option doesn't exist.")

        return True

    file = files[index]

    speak(f"Sending {file.name}.")

    ok = send_file(
        contact,
        str(file)
    )

    clear_files()

    if ok:

        speak("File sent.")

    else:

        speak("Unable to send the file.")

    return True

def whatsapp_wait_contact(data):

    set_pending_message("")

    speak("Which contact should I send it to?")

    return True

def whatsapp_wait_message(data):

    contact = data["contact"]

    set_contact(contact)

    print("[WA] Stored contact:", get_contact())

    speak(f"What would you like me to send to {contact}?")

    return True

# * =========================================================
# * WhatsApp Voice Call
# * =========================================================

def whatsapp_call(data=None):

    data = data or {}

    contact = resolve_contact(
        str(
            data.get("contact", "")
        ).strip()
    )

    if not contact:

        speak(
            "Which contact should I call?"
        )

        return True

    speak(
        f"Calling {contact} on WhatsApp."
    )

    ok = call_contact(contact)

    if not ok:

        speak(
            f"I couldn't start a WhatsApp call with {contact}."
        )

    return True

# * =========================================================
# * WhatsApp Video Call
# * =========================================================

def whatsapp_video_call(data=None):

    data = data or {}

    contact = resolve_contact(
        str(
            data.get("contact", "")
        ).strip()
    )

    if not contact:

        speak(
            "Which contact should I video call?"
        )

        return True

    speak(
        f"Starting a WhatsApp video call with {contact}."
    )

    ok = video_call_contact(contact)

    if not ok:

        speak(
            f"I couldn't start a WhatsApp video call with {contact}."
        )

    return True

register("whatsapp_open", whatsapp_open)
register("whatsapp_close", whatsapp_close)
register("whatsapp_send_message", whatsapp_send_message)
register("whatsapp_wait_message", whatsapp_wait_message)

register(
    "whatsapp_send_latest_photo",
    whatsapp_send_latest_photo
)

register(
    "whatsapp_send_latest_screenshot",
    whatsapp_send_latest_screenshot
)

register(
    "whatsapp_send_file",
    whatsapp_send_file
)

register(
    "whatsapp_send_selected_file",
    whatsapp_send_selected_file
)

register(
    "whatsapp_wait_contact",
    whatsapp_wait_contact
)

register(
    "schedule_whatsapp_message",
    schedule_whatsapp_message,
    category="communication",
)

register(
    "list_scheduled_whatsapp",
    list_scheduled_whatsapp,
    category="communication",
)

register(
    "cancel_scheduled_whatsapp",
    cancel_scheduled_whatsapp,
    category="communication",
)

register(
    "reschedule_scheduled_whatsapp",
    reschedule_scheduled_whatsapp,
    category="communication",
)

register(
    "whatsapp_call",
    whatsapp_call,
    category="communication",
)

register(
    "whatsapp_video_call",
    whatsapp_video_call,
    category="communication",
)

# * =========================================================
# * Start Scheduled WhatsApp Worker
# * =========================================================

_start_whatsapp_scheduler()
