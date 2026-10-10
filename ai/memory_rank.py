"""
JARVIS PRO
Memory Ranking

Stage 3C

Responsibilities
----------------
✓ Rank memories
✓ Prefer important memories
✓ Prefer frequently used memories
✓ Prefer recent memories
✓ Produce a final score
"""

from datetime import datetime


# * ---------------------------------------
# * Parse Time
# * ---------------------------------------

def parse_time(value):

    if not value:
        return None

    try:

        return datetime.strptime(

            value,

            "%Y-%m-%d %H:%M:%S"

        )

    except Exception:

        return None


# * ---------------------------------------
# * Rank One Memory
# * ---------------------------------------

def score(memory):

    score = 0

    # * -----------------------
    # * Importance
    # * -----------------------

    score += memory.importance * 20

    # * -----------------------
    # * Usage Count
    # * -----------------------

    score += min(

        memory.use_count,

        20

    )

    # * -----------------------
    # * Last Used Bonus
    # * -----------------------

    last = parse_time(

        memory.last_used

    )

    if last:

        days = (

            datetime.now()

            - last

        ).days

        score += max(

            0,

            30 - days

        )

    return score


# * ---------------------------------------
# * Sort Memories
# * ---------------------------------------

def rank(memories):

    return sorted(

        memories,

        key=score,

        reverse=True

    )