"""
JARVIS PRO
Memory Confidence

Stage 3B

Responsibilities
----------------
✓ Score memory confidence
✓ Detect repeated memories
✓ Detect conflicting memories
✓ Increase confidence
✓ Decrease confidence
"""

from ai.memory_store import get


# * ---------------------------------------
# * Default Scores
# * ---------------------------------------

NEW_MEMORY = 70

REPEATED_MEMORY = 100

UPDATED_MEMORY = 85

UNKNOWN_MEMORY = 0


# * ---------------------------------------
# * Confidence
# * ---------------------------------------

def confidence(key, value):
    """
    Returns confidence (0-100)

    New memory      -> 70
    Same memory     -> 100
    Updated memory  -> 85
    """

    memory = get(key)

    if not memory:
        return {

            "score": NEW_MEMORY,

            "status": "new"

        }

    if memory.value.lower() == value.lower():

        return {

            "score": REPEATED_MEMORY,

            "status": "same"

        }

    return {

        "score": UPDATED_MEMORY,

        "status": "updated",

        "old_value": memory.value

    }


# * ---------------------------------------
# * High Confidence
# * ---------------------------------------

def is_high(score):

    return score >= 90


# * ---------------------------------------
# * Medium Confidence
# * ---------------------------------------

def is_medium(score):

    return 70 <= score < 90


# * ---------------------------------------
# * Low Confidence
# * ---------------------------------------

def is_low(score):

    return score < 70