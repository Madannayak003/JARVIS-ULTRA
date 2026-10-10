"""
JARVIS PRO
Memory Profile

Stage 3D

Responsibilities
----------------
✓ Build user profile
✓ Read stored memories
✓ Human-readable summary
✓ Used by dispatcher
✓ Used by AI prompt
"""

from ai.memory_store import list_all
from config.settings import get_assistant_display_name


# * ---------------------------------------
# * Display Names
# * ---------------------------------------

DISPLAY_NAMES = {

    "name": "Name",

    "college": "College",

    "project": "Project",

    "email": "Email",

    "phone": "Phone",

    "birthday": "Birthday",

    "os": "Operating System",

    "laptop_brand": "Laptop",

    "favorite_language": "Favorite Language",

    "preferred_browser": "Preferred Browser",

    "preferred_editor": "Preferred Editor",

    "preferred_theme": "Preferred Theme",

    "favorite_drink": "Favorite Drink"

}


# * ---------------------------------------
# * Build Profile Dictionary
# * ---------------------------------------

def profile():

    memories = list_all()

    result = {}

    for memory in memories:

        result[memory.key] = memory.value

    return result


# * ---------------------------------------
# * Profile Summary
# * ---------------------------------------

def profile_summary():

    data = profile()

    if not data:

        return "I don't know anything about you yet."

    lines = []

    lines.append("==========================")

    lines.append(f"{get_assistant_display_name()} USER PROFILE")

    lines.append("==========================")

    lines.append("")

    for key, title in DISPLAY_NAMES.items():

        if key in data:

            lines.append(f"{title}")

            lines.append(data[key])

            lines.append("")

    lines.append("==========================")

    lines.append(

        f"Known Memories : {len(data)}"

    )

    return "\n".join(lines)


# * ---------------------------------------
# AI Prompt
# * ---------------------------------------

def ai_profile():

    data = profile()

    if not data:

        return ""

    text = "Known User Information\n\n"

    for key, title in DISPLAY_NAMES.items():

        if key in data:

            text += f"{title}: {data[key]}\n"

    return text
