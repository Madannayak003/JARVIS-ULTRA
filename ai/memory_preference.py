"""
JARVIS PRO
Preference Memory

Stage 3B

Responsibilities
----------------
✓ Learn user preferences
✓ Detect likes/dislikes
✓ Detect software preferences
✓ Detect editor/browser/theme
✓ Return structured memory
"""

import re


# * ---------------------------------------
# * Preference Patterns
# * ---------------------------------------

PATTERNS = [

    (r"i like (.+)", "favorite"),

    (r"i love (.+)", "favorite"),

    (r"i prefer (.+)", "preference"),

    (r"i usually use (.+)", "usage"),

    (r"i always use (.+)", "usage"),

]


# * ---------------------------------------
# * Preference Classification
# * ---------------------------------------

PREFERENCE_KEYS = {

    # * Languages
    "python": "favorite_language",
    "c++": "favorite_language",
    "c": "favorite_language",
    "java": "favorite_language",
    "javascript": "favorite_language",
    "typescript": "favorite_language",

    # * Browsers
    "chrome": "preferred_browser",
    "google chrome": "preferred_browser",
    "edge": "preferred_browser",
    "firefox": "preferred_browser",
    "brave": "preferred_browser",
    "opera": "preferred_browser",

    # * Editors
    "vs code": "preferred_editor",
    "vscode": "preferred_editor",
    "visual studio code": "preferred_editor",
    "pycharm": "preferred_editor",
    "cursor": "preferred_editor",

    # * Theme
    "dark mode": "preferred_theme",
    "light mode": "preferred_theme",

    # * Drinks
    "coffee": "favorite_drink",
    "tea": "favorite_drink",

    # * OS
    "windows": "preferred_os",
    "windows 11": "preferred_os",
    "linux": "preferred_os",
    "ubuntu": "preferred_os",

}


# * ---------------------------------------
# * Normalize Value
# * ---------------------------------------

def clean(value):

    return (

        value

        .strip()

        .strip(".,!?")

    )


# * ---------------------------------------
# * Extract Preference
# * ---------------------------------------

def extract(text):

    text = text.strip().lower()

    for pattern, _ in PATTERNS:

        match = re.match(pattern, text)

        if not match:
            continue

        value = clean(match.group(1))

        key = PREFERENCE_KEYS.get(

            value.lower(),

            "preference"

        )

        return {

            "remember": True,

            "key": key,

            "value": value.title(),

            "category": "preference",

            "importance": 2

        }

    return {

        "remember": False

    }