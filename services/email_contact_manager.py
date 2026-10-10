"""
JARVIS PRO
Email Contact Manager

Responsibilities:
- Load email contacts
- Save email contacts
- Add email contacts
- Resolve email aliases
- Remove email contacts
- List email contacts
"""

import json
from pathlib import Path


# * =========================================================
# * Configuration
# * =========================================================

EMAIL_CONTACTS_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "email_contacts.json"
)


# * =========================================================
# * Load Contacts
# * =========================================================

def load_email_contacts():

    if not EMAIL_CONTACTS_FILE.exists():

        EMAIL_CONTACTS_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        EMAIL_CONTACTS_FILE.write_text(
            "{}",
            encoding="utf-8"
        )

    try:

        with open(
            EMAIL_CONTACTS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

            if isinstance(data, dict):
                return data

    except Exception as error:

        print(
            f"[EMAIL CONTACT ERROR] "
            f"Could not load contacts: {error}"
        )

    return {}


# * =========================================================
# * Save Contacts
# * =========================================================

def save_email_contacts(contacts):

    with open(
        EMAIL_CONTACTS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            contacts,
            file,
            indent=4,
            ensure_ascii=False
        )


# * =========================================================
# * Add Contact
# * =========================================================

def add_email_contact(alias, email):

    alias = str(
        alias or ""
    ).strip().lower()

    email = str(
        email or ""
    ).strip()

    if not alias:
        raise ValueError(
            "Email contact alias is required."
        )

    if not email:
        raise ValueError(
            "Email address is required."
        )

    contacts = load_email_contacts()

    contacts[alias] = email

    save_email_contacts(
        contacts
    )

    print(
        f"[EMAIL CONTACT] Added: "
        f"{alias} -> {email}"
    )

    return True


# * =========================================================
# * Get Contact
# * =========================================================

def get_email_contact(alias):

    alias = str(
        alias or ""
    ).strip().lower()

    contacts = load_email_contacts()

    return contacts.get(
        alias
    )


# * =========================================================
# * Resolve Contact
# * =========================================================

def resolve_email_contact(value):

    value = str(
        value or ""
    ).strip()

    if not value:
        return value

    contact = get_email_contact(
        value
    )

    if contact:
        return contact

    return value


# * =========================================================
# * Remove Contact
# * =========================================================

def remove_email_contact(alias):

    alias = str(
        alias or ""
    ).strip().lower()

    contacts = load_email_contacts()

    if alias not in contacts:
        return False

    del contacts[alias]

    save_email_contacts(
        contacts
    )

    print(
        f"[EMAIL CONTACT] Removed: {alias}"
    )

    return True


# * =========================================================
# * List Contacts
# * =========================================================

def list_email_contacts():

    return load_email_contacts()


# * =========================================================
# * Contact Exists
# * =========================================================

def email_contact_exists(alias):

    alias = str(
        alias or ""
    ).strip().lower()

    contacts = load_email_contacts()

    return alias in contacts


# * =========================================================
# * Total Contacts
# * =========================================================

def total_email_contacts():

    return len(
        load_email_contacts()
    )