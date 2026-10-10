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

        return True

    add_contact(alias, real_name)

    speak(f"I'll remember {real_name} as {alias}.")

    return True


# * --------------------------------------------------
# * Forget Contact
# * --------------------------------------------------

def forget_contact(data):

    alias = data.get("alias", "").strip()

    if not alias:

        speak("Which contact should I forget?")

        return True

    if remove_contact(alias):

        speak(f"I've forgotten {alias}.")

    else:

        speak(f"I couldn't find {alias} in your contacts.")

    return True


# * --------------------------------------------------
# * List Contacts
# * --------------------------------------------------

def show_contacts(data):

    contacts = list_contacts()

    if not contacts:

        speak("You don't have any saved contacts yet.")

        return True

    speak(f"You have {len(contacts)} saved contacts.")

    print("\n========== SAVED CONTACTS ==========\n")

    for alias, name in contacts.items():

        print(f"{alias}  ->  {name}")

    print("\n===================================\n")

    return True


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