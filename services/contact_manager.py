import json
from pathlib import Path

# * ---------------------------------------
# * Database Location
# * ---------------------------------------

CONTACTS_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "contacts.json"
)


# * ---------------------------------------
# * Internal Helpers
# * ---------------------------------------

def load_contacts():

    if not CONTACTS_FILE.exists():

        CONTACTS_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        CONTACTS_FILE.write_text(
            "{}",
            encoding="utf-8"
        )

    try:

        with open(
            CONTACTS_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return {}


def save_contacts(contacts):

    with open(
        CONTACTS_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            contacts,
            f,
            indent=4,
            ensure_ascii=False
        )


# * ---------------------------------------
# * Public API
# * ---------------------------------------

def add_contact(alias, real_name):

    contacts = load_contacts()

    alias = alias.strip().lower()
    real_name = real_name.strip()

    contacts[alias] = real_name

    save_contacts(contacts)

    return True


def get_contact(alias):

    contacts = load_contacts()

    return contacts.get(
        alias.strip().lower()
    )


def resolve_contact(name):

    """
    Returns the saved contact name if it exists.
    Otherwise returns the original text.
    """

    contact = get_contact(name)

    if contact:

        return contact

    return name


def remove_contact(alias):

    contacts = load_contacts()

    alias = alias.strip().lower()

    if alias in contacts:

        del contacts[alias]

        save_contacts(contacts)

        return True

    return False


def list_contacts():

    return load_contacts()


def contact_exists(alias):

    contacts = load_contacts()

    return alias.strip().lower() in contacts


def total_contacts():

    return len(load_contacts())