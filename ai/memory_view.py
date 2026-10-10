"""
JARVIS PRO
Memory View

Stage 2C

Responsibilities
----------------
✓ Show all memories
✓ Show one memory
✓ Show memories by category
✓ Pretty formatting
"""

from ai.memory_store import (
    list_all,
    get
)


# * ---------------------------------------
# * Show All
# * ---------------------------------------

def show_all():

    memories = list_all()

    if not memories:

        return "I don't know anything about you yet."

    lines = []

    for memory in memories:

        lines.append(

            f"{memory.key} : {memory.value}"

        )

    return "\n".join(lines)


# * ---------------------------------------
# * Show One
# * ---------------------------------------

def show(key):

    memory = get(key)

    if not memory:

        return None

    return f"{memory.key} : {memory.value}"


# * ---------------------------------------
# * Show Category
# * ---------------------------------------

def show_category(category):

    memories = [

        m

        for m in list_all()

        if m.category.lower() == category.lower()

    ]

    if not memories:

        return None

    lines = []

    for memory in memories:

        lines.append(

            f"{memory.key} : {memory.value}"

        )

    return "\n".join(lines)


# * ---------------------------------------
# * Pretty View
# * ---------------------------------------

def pretty():

    memories = list_all()

    if not memories:

        return "Memory is empty."

    width = max(

        len(m.key)

        for m in memories

    )

    lines = []

    for memory in memories:

        lines.append(

            f"{memory.key.ljust(width)} : {memory.value}"

        )

    return "\n".join(lines)