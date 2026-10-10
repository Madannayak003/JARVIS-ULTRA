"""
JARVIS PRO
Memory Intent

Responsibilities
----------------
✓ Detect forget requests
✓ Detect forget target
✓ Route to memory_forget
"""

from ai.memory_forget import (
    forget_key,
    forget_category,
    forget_all,
)


# * ---------------------------------------
# * Memory Keys
# * ---------------------------------------

KEY_ALIASES = {

    "name": ["name"],

    "college": [
        "college",
        "university",
        "school"
    ],

    "project": [
        "project"
    ],

    "email": [
        "email",
        "mail",
        "gmail"
    ],

    "phone": [
        "phone",
        "mobile",
        "number"
    ],

    "birthday": [
        "birthday",
        "birth date"
    ],

    "favorite_language": [
        "favorite language",
        "favourite language",
        "programming language"
    ],

    "os": [
        "operating system",
        "windows",
        "os"
    ],

    "laptop_brand": [
        "laptop",
        "computer",
        "pc"
    ]
}


# * ---------------------------------------
# * Categories
# * ---------------------------------------

CATEGORY_ALIASES = {

    "education": [
        "education"
    ],

    "contact": [
        "contact"
    ],

    "device": [
        "device"
    ],

    "identity": [
        "identity"
    ],

    "project": [
        "project"
    ],

    "personal": [
        "personal"
    ]
}


# * ---------------------------------------
# * Handle Intent
# * ---------------------------------------

def handle(text):

    text = text.lower().strip()

    # * -------------------------
    # * Forget Key
    # * -------------------------

    if (
        "forget" in text
        or "delete" in text
        or "remove" in text
    ):

        for key, aliases in KEY_ALIASES.items():

            for alias in aliases:

                if alias in text:

                    return forget_key(key)

    # * -------------------------
    # * Forget Category
    # * -------------------------

    if (
        "forget" in text
        or "delete" in text
        or "remove" in text
    ):

        for category, aliases in CATEGORY_ALIASES.items():

            for alias in aliases:

                if (
                    alias in text
                    and (
                        "about" in text
                        or "category" in text
                    )
                ):

                    return forget_category(category)

    # * -------------------------
    # * Forget Everything
    # * -------------------------

    if text in {

        "forget everything",

        "delete everything",

        "clear memory",

        "clear all memory",

        "forget all memories",

        "forget everything about me",

        "delete all memories"

    }:

        return forget_all()

    return None