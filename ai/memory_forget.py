"""
JARVIS PRO
Memory Forget

Responsibilities
----------------
✓ Forget one memory
✓ Forget by category
✓ Forget everything
"""

from ai.memory_store import (
    forget,
    list_all,
)


# * ---------------------------------------
# * Forget by Key
# * ---------------------------------------

def forget_key(key):

    forget(key)

    return {

        "success": True,

        "type": "key",

        "key": key

    }


# * ---------------------------------------
# * Forget by Category
# * ---------------------------------------

def forget_category(category):

    deleted = []

    memories = list_all()

    for memory in memories:

        if memory.category.lower() == category.lower():

            forget(memory.key)

            deleted.append(memory.key)

    return {

        "success": True,

        "type": "category",

        "category": category,

        "deleted": deleted

    }


# * ---------------------------------------
# * Forget Everything
# * ---------------------------------------

def forget_all():

    memories = list_all()

    deleted = []

    for memory in memories:

        forget(memory.key)

        deleted.append(memory.key)

    return {

        "success": True,

        "type": "all",

        "deleted": deleted

    }