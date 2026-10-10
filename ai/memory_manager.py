"""
JARVIS PRO
Memory Manager

Stage 1
--------

Responsibilities

✓ Detect remember-worthy facts
✓ Extract key/value
✓ Save memory
✓ Ignore normal conversation
"""

import re

from ai.memory_store import (
    remember,
    get
)


# * ---------------------------------------
# * Rules
# * ---------------------------------------

RULES = [

    (
        r"^my name is (.+)$",
        "name",
        "identity",
        "name,user,identity",
        5
    ),

    (
        r"^i am ([A-Za-z][A-Za-z .'-]{0,58})$",
        "name",
        "identity",
        "name,user,identity",
        5
    ),

    (
        r"my college is (.+)",
        "college",
        "education",
        "college,education",
        4
    ),

    (
        r"i study at (.+)",
        "college",
        "education",
        "college,education",
        4
    ),

    (
        r"my project is (.+)",
        "project",
        "project",
        "project",
        4
    ),

    (
        r"my birthday is (.+)",
        "birthday",
        "personal",
        "birthday,date",
        4
    ),

    (
        r"my phone number is (.+)",
        "phone",
        "contact",
        "phone,mobile,number",
        5
    ),

    (
        r"my email is (.+)",
        "email",
        "contact",
        "email,mail",
        5
    ),

    (
        r"my favourite language is (.+)",
        "favorite_language",
        "preference",
        "language,favorite",
        3
    ),

    (
        r"my favorite language is (.+)",
        "favorite_language",
        "preference",
        "language,favorite",
        3
    ),
]


# * ---------------------------------------
# * Clean Value
# * ---------------------------------------

def clean_value(value, key=None):

    value = value.strip()
    value = " ".join(value.split())

    # * Preserve email exactly
    if key == "email":
        return value.lower()

    # * Preserve phone numbers
    if key == "phone":
        return value

    # * Title-case only names/titles
    if len(value) < 60:
        value = value.title()

    return value


# * ---------------------------------------
# * Learn
# * ---------------------------------------

def learn(text):

    original_text = text.strip()

    for pattern, key, category, keywords, importance in RULES:

        match = re.fullmatch(
            pattern,
            original_text,
            re.IGNORECASE
        )

        if not match:
            continue

        value = clean_value(
            match.group(1), key
        )

        if not value:

            return {

                "saved": False,

                "reason": "empty"

            }

        existing = get(key)

        # * -------------------------
        # * Already Known
        # * -------------------------

        if existing:

            if existing.value.lower() == value.lower():

                print("\n[MEMORY MANAGER]")

                print("Already Known")

                print("Key   :", key)

                print("Value :", existing.value)

                return {

                    "saved": False,

                    "already_known": True,

                    "memory": existing

                }

        # * -------------------------
        # * Updated
        # * -------------------------

        updated = False
        old_value = None

        if existing:

            updated = True

            old_value = existing.value
            
        # * -------------------------
        # ! Debug
        # * -------------------------

        print("\n[MEMORY MANAGER]")

        print("Pattern   :", pattern)

        print("Key       :", key)

        print("Value     :", value)

        print("Category  :", category)

        print("Importance:", importance)

        print("Updated   :", updated)

        if updated:

            print("Old Value :", old_value)    
            
        # * -------------------------
        # * Save Memory
        # * -------------------------

        remember(

            key=key,

            value=value,

            category=category,

            keywords=keywords,

            importance=importance

        )

        return {

            "saved": True,

            "updated": updated,

            "already_known": False,

            "old_value": old_value,

            "key": key,

            "value": value,

            "category": category,

            "importance": importance

        }
        
    print("\n[MEMORY MANAGER]")

    print("No memory rule matched.")    

    return {

        "saved": False

    }