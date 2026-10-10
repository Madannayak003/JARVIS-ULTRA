"""
JARVIS PRO
Memory Statistics

Responsibilities
----------------
✓ Memory statistics
✓ Category statistics
✓ Usage statistics
✓ Recently updated
✓ Recently used
"""

from ai.memory_store import list_all


# * ---------------------------------------
# * Total Memories
# * ---------------------------------------

def total():

    return len(list_all())


# * ---------------------------------------
# * Count By Category
# * ---------------------------------------

def by_category():

    stats = {}

    for memory in list_all():

        category = memory.category

        stats[category] = (

            stats.get(category, 0) + 1

        )

    return stats


# * ---------------------------------------
# * Most Used Memories
# * ---------------------------------------

def most_used(limit=10):

    memories = sorted(

        list_all(),

        key=lambda m: m.use_count,

        reverse=True

    )

    return memories[:limit]


# * ---------------------------------------
# * Least Used Memories
# * ---------------------------------------

def least_used(limit=10):

    memories = sorted(

        list_all(),

        key=lambda m: m.use_count

    )

    return memories[:limit]


# * ---------------------------------------
# * Recently Updated
# * ---------------------------------------

def recent(limit=10):

    memories = sorted(

        list_all(),

        key=lambda m: m.updated_at,

        reverse=True

    )

    return memories[:limit]


# * ---------------------------------------
# ! Never Used
# * ---------------------------------------

def unused(limit=10):

    memories = [

        m

        for m in list_all()

        if m.use_count == 0

    ]

    return memories[:limit]


# * ---------------------------------------
# * Full Statistics
# * ---------------------------------------

def stats():

    return {

        "total": total(),

        "categories": by_category(),

        "most_used": [

            m.key

            for m in most_used()

        ],

        "least_used": [

            m.key

            for m in least_used()

        ],

        "unused": [

            m.key

            for m in unused()

        ]

    }