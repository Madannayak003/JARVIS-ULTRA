"""
JARVIS PRO
Email Skill

Responsibilities:
- Send emails through Gmail
- Manage multi-step email composition
- Provide JARVIS voice feedback
"""

from core.registry import register
from voice.manager import speak

from services.gmail_service import send_email as gmail_send_email

from services.email_contact_manager import (
    resolve_email_contact,
)

from services.email_contact_manager import (
    resolve_email_contact,
    add_email_contact,
    remove_email_contact,
    list_email_contacts,
)


# * =========================================================
# * Pending Email Draft
# * =========================================================

_PENDING_EMAIL = None


def has_pending_email():
    """
    Return True when JARVIS is waiting for an email field.
    """

    return _PENDING_EMAIL is not None


def clear_email_draft():
    """
    Clear the current pending email draft.
    """

    global _PENDING_EMAIL

    _PENDING_EMAIL = None


def start_email_draft(recipient):
    """
    Start a new multi-step email draft.
    """

    global _PENDING_EMAIL

    recipient = str(
        recipient or ""
    ).strip()

    recipient = resolve_email_contact(
        recipient
    )

    if not recipient:

        speak(
            "Please provide the recipient email address."
        )

        return False

    _PENDING_EMAIL = {
        "recipient": recipient,
        "subject": "",
        "body": "",
        "stage": "subject",
    }

    print(
        "[EMAIL] Draft started."
    )

    print(
        f"[EMAIL] Recipient: {recipient}"
    )

    speak(
        "What is the subject?"
    )

    return True


def handle_email_reply(command):
    """
    Handle the next response while composing an email.
    """

    global _PENDING_EMAIL

    if _PENDING_EMAIL is None:
        return False

    command = str(
        command or ""
    ).strip()

    if not command:
        return True

    # * -----------------------------------------------------
    # * Subject
    # * -----------------------------------------------------

    if _PENDING_EMAIL["stage"] == "subject":

        _PENDING_EMAIL["subject"] = command

        _PENDING_EMAIL["stage"] = "body"

        print(
            f"[EMAIL] Subject: {command}"
        )

        speak(
            "What should I say?"
        )

        return True

    # * -----------------------------------------------------
    # * Body
    # * -----------------------------------------------------

    if _PENDING_EMAIL["stage"] == "body":

        _PENDING_EMAIL["body"] = command

        recipient = _PENDING_EMAIL["recipient"]
        subject = _PENDING_EMAIL["subject"]
        body = _PENDING_EMAIL["body"]

        print(
            f"[EMAIL] To: {recipient}"
        )

        print(
            f"[EMAIL] Subject: {subject}"
        )

        print(
            f"[EMAIL] Body: {body}"
        )

        try:

            gmail_send_email(
                recipient=recipient,
                subject=subject,
                body=body,
            )

        except Exception as error:

            print(
                f"[EMAIL ERROR] {error}"
            )

            clear_email_draft()

            speak(
                "I could not send the email."
            )

            return False

        clear_email_draft()

        print(
            "[EMAIL] Email sent successfully."
        )

        speak(
            "Email sent successfully."
        )

        return True

    return False


# * =========================================================
# * Send Email Action
# * =========================================================

def send_email(data=None):

    data = data or {}

    recipient = str(
        data.get("recipient", "")
    ).strip()

    subject = str(
        data.get("subject", "")
    ).strip()

    body = str(
        data.get("body", "")
    ).strip()

    if not recipient:

        speak(
            "Please provide the recipient email address."
        )

        return False

    # * -----------------------------------------------------
    # * Complete email supplied directly
    # * -----------------------------------------------------

    if subject and body:

        print(
            f"[EMAIL] To: {recipient}"
        )

        print(
            f"[EMAIL] Subject: {subject}"
        )

        print(
            f"[EMAIL] Body: {body}"
        )

        try:

            gmail_send_email(
                recipient=recipient,
                subject=subject,
                body=body,
            )

        except Exception as error:

            print(
                f"[EMAIL ERROR] {error}"
            )

            speak(
                "I could not send the email."
            )

            return False

        print(
            "[EMAIL] Email sent successfully."
        )

        speak(
            "Email sent successfully."
        )

        return True

    # * -----------------------------------------------------
    # * Start multi-step composition
    # * -----------------------------------------------------

    return start_email_draft(
        recipient
    )

# * =========================================================
# * Remember Email Contact
# * =========================================================

def remember_email_contact(data=None):

    data = data or {}

    alias = str(
        data.get("alias", "")
    ).strip()

    email = str(
        data.get("email", "")
    ).strip()

    if not alias:

        speak(
            "Please provide the email contact name."
        )

        return False

    if not email:

        speak(
            "Please provide the email address."
        )

        return False

    try:

        add_email_contact(
            alias,
            email,
        )

    except Exception as error:

        print(
            f"[EMAIL CONTACT ERROR] {error}"
        )

        speak(
            "I could not save that email contact."
        )

        return False

    speak(
        f"Email contact {alias} saved successfully."
    )

    return True


# * =========================================================
# * Forget Email Contact
# * =========================================================

def forget_email_contact(data=None):

    data = data or {}

    alias = str(
        data.get("alias", "")
    ).strip()

    if not alias:

        speak(
            "Please provide the email contact name."
        )

        return False

    removed = remove_email_contact(
        alias
    )

    if not removed:

        speak(
            f"I could not find an email contact named {alias}."
        )

        return False

    speak(
        f"Email contact {alias} removed successfully."
    )

    return True


# * =========================================================
# * Show Email Contacts
# * =========================================================

def show_email_contacts(data=None):

    contacts = list_email_contacts()

    if not contacts:

        speak(
            "There are no saved email contacts."
        )

        return True

    print(
        "[EMAIL CONTACTS]"
    )

    for alias, email in contacts.items():

        print(
            f"[EMAIL CONTACT] {alias}: {email}"
        )

    contact_text = ", ".join(
        f"{alias}: {email}"
        for alias, email in contacts.items()
    )

    speak(
        f"Your saved email contacts are: {contact_text}"
    )

    return True

# * =========================================================
# * Register Skills
# * =========================================================

register(
    "send_email",
    send_email
)

register(
    "remember_email_contact",
    remember_email_contact
)

register(
    "forget_email_contact",
    forget_email_contact
)

register(
    "show_email_contacts",
    show_email_contacts
)


print(
    "[EMAIL] Skill loaded"
)