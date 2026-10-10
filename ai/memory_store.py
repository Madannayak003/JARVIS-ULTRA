"""
JARVIS PRO
Memory Store

Responsibilities
----------------
✓ Remember
✓ Update
✓ Delete
✓ Read
✓ List
✓ Statistics
✓ Touch Memory
"""

from ai.memory import connect
from ai.memory_schema import (
    Memory,
    now,
    MEDIUM,
    OTHER
)


# * ---------------------------------------
# * Save / Update Memory
# * ---------------------------------------

def remember(

    key,
    value,
    category=OTHER,
    keywords="",
    importance=MEDIUM

):

    conn = connect()

    cursor = conn.cursor()

    timestamp = now()

    cursor.execute("""

        INSERT INTO memories(

            key,
            value,
            category,
            keywords,
            importance,
            created_at,
            updated_at

        )

        VALUES(?,?,?,?,?,?,?)

        ON CONFLICT(key)

        DO UPDATE SET

            value=excluded.value,

            category=excluded.category,

            keywords=excluded.keywords,

            importance=excluded.importance,

            updated_at=excluded.updated_at

    """, (

        key,

        value,

        category,

        keywords,

        importance,

        timestamp,

        timestamp

    ))

    conn.commit()

    conn.close()

    return True


# * ---------------------------------------
# * Get One Memory
# * ---------------------------------------

def get(key):

    conn = connect()

    cursor = conn.cursor()

    cursor.execute(

        "SELECT * FROM memories WHERE key=?",

        (key,)

    )

    row = cursor.fetchone()

    conn.close()

    if not row:

        return None

    return Memory(

        id=row["id"],

        key=row["key"],

        value=row["value"],

        category=row["category"],

        keywords=row["keywords"],

        importance=row["importance"],

        created_at=row["created_at"],

        updated_at=row["updated_at"],

        last_used=row["last_used"],

        use_count=row["use_count"]

    )


# * ---------------------------------------
# * Exists
# * ---------------------------------------

def exists(key):

    return get(key) is not None


# * ---------------------------------------
# * Delete
# * ---------------------------------------

def forget(key):

    conn = connect()

    cursor = conn.cursor()

    cursor.execute(

        "DELETE FROM memories WHERE key=?",

        (key,)

    )

    conn.commit()

    conn.close()

    return True


# * ---------------------------------------
# * List All
# * ---------------------------------------

def list_all():

    conn = connect()

    cursor = conn.cursor()

    cursor.execute("""

        SELECT *

        FROM memories

        ORDER BY updated_at DESC

    """)

    rows = cursor.fetchall()

    conn.close()

    return [

        Memory(

            id=row["id"],

            key=row["key"],

            value=row["value"],

            category=row["category"],

            keywords=row["keywords"],

            importance=row["importance"],

            created_at=row["created_at"],

            updated_at=row["updated_at"],

            last_used=row["last_used"],

            use_count=row["use_count"]

        )

        for row in rows

    ]


# * ---------------------------------------
# * Memory Count
# * ---------------------------------------

def total():

    conn = connect()

    cursor = conn.cursor()

    cursor.execute(

        "SELECT COUNT(*) FROM memories"

    )

    count = cursor.fetchone()[0]

    conn.close()

    return count


# * ---------------------------------------
# * Update Last Used
# * ---------------------------------------

def touch(key):

    conn = connect()

    cursor = conn.cursor()

    cursor.execute("""

        UPDATE memories

        SET

            last_used=?,

            use_count=use_count+1

        WHERE key=?

    """, (

        now(),

        key

    ))

    conn.commit()

    conn.close()
    
# * ---------------------------------------
# * All Memories
# * ---------------------------------------
    
def all_memories():

        conn = connect()

        cursor = conn.cursor()

        cursor.execute("""

            SELECT *

            FROM memories

            ORDER BY updated_at DESC

        """)

        rows = cursor.fetchall()

        conn.close()

        memories = []

        for row in rows:

            memories.append(

                Memory(

                    id=row["id"],

                    key=row["key"],

                    value=row["value"],

                    category=row["category"],

                    keywords=row["keywords"],

                    importance=row["importance"],

                    created_at=row["created_at"],

                    updated_at=row["updated_at"],

                    last_used=row["last_used"],

                    use_count=row["use_count"]

                )

            )

        return memories