"""
JARVIS PRO
Core Skill Registry

Registry V3

Responsibilities:

- Register skill actions
- Categorize skill actions
- Execute registered actions
- Validate registrations
- Prevent accidental invalid registrations
- Provide registry inspection helpers
- Preserve compatibility with existing skills
"""

from core.fallback import fallback
from core.diagnostics import debug_print

from core.skill_categories import (
    get_category,
    list_categories,
)


# * =========================================================
# * Skill Registry
# * =========================================================

SKILLS = {}

# * action -> category
SKILL_CATEGORIES = {}


# * =========================================================
# * Register
# * =========================================================

def register(
    action,
    handler,
    category=None,
):
    """
    Register a skill action.

    Existing skills remain backward compatible:

        register("action_name", handler)

    New or updated skills can specify:

        register(
            "action_name",
            handler,
            category="system",
        )
    """

    if not isinstance(action, str):
        raise TypeError(
            "Skill action must be a string."
        )

    action = action.strip()

    if not action:
        raise ValueError(
            "Skill action cannot be empty."
        )

    if not callable(handler):
        raise TypeError(
            f"Handler for '{action}' must be callable."
        )

    # * -----------------------------------------
    # * Category
    # * -----------------------------------------

    if category is None:
        category = get_category(action)

    if not isinstance(category, str):
        raise TypeError(
            f"Category for '{action}' must be a string."
        )

    category = category.strip().lower()

    if not category:
        category = "uncategorized"

    # * -----------------------------------------
    # * Duplicate registration
    # * -----------------------------------------

    existing = SKILLS.get(action)

    if existing is not None and existing is not handler:

        print(
            f"[REGISTRY WARNING] "
            f"Replacing existing handler for '{action}'"
        )

    # * -----------------------------------------
    # * Store
    # * -----------------------------------------

    SKILLS[action] = handler

    SKILL_CATEGORIES[action] = category


# * =========================================================
# * Unregister
# * =========================================================

def unregister(action):
    """
    Remove a registered action.

    Returns:
        True  -> removed
        False -> action was not registered
    """

    if not isinstance(action, str):
        return False

    action = action.strip()

    if action in SKILLS:

        del SKILLS[action]

        SKILL_CATEGORIES.pop(
            action,
            None,
        )

        return True

    return False


# * =========================================================
# * Get Handler
# * =========================================================

def get_handler(action):
    """
    Return the handler registered for an action.

    Returns:
        handler or None
    """

    if not isinstance(action, str):
        return None

    return SKILLS.get(
        action.strip()
    )


# * =========================================================
# * Has Skill
# * =========================================================

def has_skill(action):
    """
    Check whether an action is registered.
    """

    if not isinstance(action, str):
        return False

    return action.strip() in SKILLS


# * =========================================================
# * Get Category
# * =========================================================

def get_skill_category(action):
    """
    Return the category of a registered action.

    Returns:
        category name or None
    """

    if not isinstance(action, str):
        return None

    action = action.strip()

    if action not in SKILLS:
        return None

    return SKILL_CATEGORIES.get(
        action,
        "uncategorized",
    )


# * =========================================================
# * Execute
# * =========================================================

def execute(action, data=None):
    """
    Execute a registered skill action.

    Falls back to the AI fallback system when
    the action is unknown.
    """

    if not isinstance(action, str):

        print(
            f"[REGISTRY ERROR] Invalid action: {action!r}"
        )

        return False

    action = action.strip()

    debug_print(
        "Requested action :",
        repr(action),
    )

    debug_print(
        "Category         :",
        get_skill_category(action),
    )

    debug_print(
        "Available actions:",
        sorted(SKILLS.keys()),
    )

    handler = get_handler(action)

    # * -----------------------------------------
    # * Registered skill
    # * -----------------------------------------

    if handler:

        try:

            return handler(data)

        except Exception as e:

            print(
                f"[REGISTRY ERROR] "
                f"Action '{action}' failed:"
            )

            print(e)

            return False

    # * -----------------------------------------
    # * Unknown action
    # * -----------------------------------------

    print(
        f"\nUnknown action : {action}"
    )

    print(
        "\nTrying AI fallback...\n"
    )

    try:

        result = fallback(action)

        print(result)

        return result

    except Exception as e:

        print(
            f"[REGISTRY FALLBACK ERROR] {e}"
        )

        return False


# * =========================================================
# * List Skills
# * =========================================================

def list_skills():
    """
    Return all registered skill actions.
    """

    return list(
        SKILLS.keys()
    )


# * =========================================================
# * Skill Count
# * =========================================================

def skill_count():
    """
    Return the number of registered actions.
    """

    return len(SKILLS)


# * =========================================================
# * List Categories
# * =========================================================

def list_skill_categories():
    """
    Return categories currently used by registered actions.
    """

    return sorted(
        set(
            SKILL_CATEGORIES.values()
        )
    )


# * =========================================================
# * List Skills By Category
# * =========================================================

def list_skills_by_category(category):
    """
    Return registered actions belonging to a category.
    """

    if not isinstance(category, str):
        return []

    category = category.strip().lower()

    return sorted(
        action
        for action, action_category
        in SKILL_CATEGORIES.items()
        if action_category == category
        and action in SKILLS
    )


# * =========================================================
# * Categorized Skills
# * =========================================================

def categorized_skills():
    """
    Return all registered actions grouped by category.
    """

    result = {}

    for action in SKILLS:

        category = SKILL_CATEGORIES.get(
            action,
            "uncategorized",
        )

        result.setdefault(
            category,
            [],
        )

        result[category].append(
            action
        )

    for category in result:

        result[category].sort()

    return dict(
        sorted(result.items())
    )


# * =========================================================
# * Registry Information
# * =========================================================

def registry_info():
    """
    Return complete registry diagnostics.
    """

    grouped = categorized_skills()

    return {
        "count": len(SKILLS),

        "categories": len(grouped),

        "category_counts": {
            category: len(actions)
            for category, actions
            in grouped.items()
        },

        "actions": sorted(
            SKILLS.keys()
        ),

        "categorized_skills": grouped,
    }
