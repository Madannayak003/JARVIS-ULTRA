from core.registry import register
from voice.manager import speak

from services.contact_manager import (
    add_contact,
    remove_contact,
    list_contacts
)


# * --------------------------------------------------
# * Remember Contact
# * --------------------------------------------------

def remember_contact(data):

    alias = data.get("alias", "").strip()
    real_name = data.get("real_name", "").strip()

    if not alias or not real_name:

        speak("Please tell me both the alias and the contact name.")

        return False

    try:
        saved = add_contact(alias, real_name)
    except Exception as error:
        print(f"[CONTACT ERROR] Save failed: {error}")
        speak("I couldn't remember that contact.")
        return False

    if not saved:
        speak("I couldn't remember that contact.")
        return False

    speak(f"I'll remember {real_name} as {alias}.")

    return {
        "ok": True,
        "status": "reported_success",
        "action": "remember_contact",
        "alias": alias.lower(),
        "real_name": real_name,
    }


# * --------------------------------------------------
# * Forget Contact
# * --------------------------------------------------

def forget_contact(data):

    alias = data.get("alias", "").strip()

    if not alias:

        speak("Which contact should I forget?")

        return False

    try:
        removed = remove_contact(alias)
    except Exception as error:
        print(f"[CONTACT ERROR] Remove failed: {error}")
        speak(f"I couldn't forget {alias}.")
        return False

    if not removed:
        speak(f"I couldn't find {alias} in your contacts.")
        return False

    speak(f"I've forgotten {alias}.")
    return {
        "ok": True,
        "status": "reported_success",
        "action": "forget_contact",
        "alias": alias.lower(),
    }


# * --------------------------------------------------
# * List Contacts
# * --------------------------------------------------

def show_contacts(data):

    contacts = list_contacts()

    if not contacts:

        speak("You don't have any saved contacts yet.")

        return {"ok": True, "status": "no_results", "action": "show_contacts", "items": {}, "count": 0}

    speak(f"You have {len(contacts)} saved contacts.")

    print("\n========== SAVED CONTACTS ==========\n")

    for alias, name in contacts.items():

        print(f"{alias}  ->  {name}")

    print("\n===================================\n")

    return {"ok": True, "status": "reported_success", "action": "show_contacts", "items": dict(contacts), "count": len(contacts)}


# * --------------------------------------------------
# * Register Skills
# * --------------------------------------------------

register(
    "remember_contact",
    remember_contact
)

register(
    "forget_contact",
    forget_contact
)

register(
    "show_contacts",
    show_contacts
)

print("[CONTACT] Skill loaded")
