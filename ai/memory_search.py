"""
JARVIS PRO
Memory Search Engine

Responsibilities
----------------
✓ Search memories
✓ Rank memories
✓ Keyword matching
✓ Category filtering
✓ Return only relevant memories
"""

from ai.memory import connect
from ai.memory_rank import rank
from ai.memory_store import touch
from ai.memory_schema import Memory
from ai.query_parser import extract_keywords
from ai.memory_confidence import confidence

MIN_SCORE = 40

# * ---------------------------------------
# * Score a Memory
# * ---------------------------------------

def score_memory(memory, keywords):

    score = 0

    # * -----------------------
    # * Exact Key Match
    # * -----------------------

    for word in keywords:

        if word == memory.key.lower():

            score += 120

        elif word in memory.key.lower():

            score += 80

    # * -----------------------
    # * Value Match
    # * -----------------------

    if memory.value:

        value = memory.value.lower()

        for word in keywords:

            if word in value:

                score += 40

    # * -----------------------
    # * Keyword Match
    # * -----------------------

    if memory.keywords:

        db_keywords = [

            k.strip()

            for k in memory.keywords.lower().split(",")

        ]

        for word in keywords:

            if word in db_keywords:

                score += 35

    # * -----------------------
    # * Category Match
    # * -----------------------

    if memory.category:

        if memory.category.lower() in keywords:

            score += 20

    # * -----------------------
    # * Importance Bonus
    # * -----------------------

    score += memory.importance * 10

    # * -----------------------
    # * Frequently Used Bonus
    # * -----------------------

    score += min(memory.use_count * 2, 20)

    # * -----------------------
    # * Exact Value Bonus
    # * -----------------------

    if memory.value:

        value = memory.value.lower()

        if value in " ".join(keywords):

            score += 50

    return score


# * ---------------------------------------
# * Search
# * ---------------------------------------

def search(query, limit=5):

    keywords = extract_keywords(query)

    if not keywords:
        return []

    conn = connect()

    cursor = conn.cursor()

    candidates = {}

    # * ---------------------------------------
    # * Find Candidate Memories
    # * ---------------------------------------

    for word in keywords:

        cursor.execute("""

            SELECT *

            FROM memories

            WHERE

                LOWER(key) LIKE ?

                OR LOWER(value) LIKE ?

                OR LOWER(keywords) LIKE ?

                OR LOWER(category) LIKE ?

        """, (

            f"%{word}%",

            f"%{word}%",

            f"%{word}%",

            f"%{word}%"

        ))

        for row in cursor.fetchall():

            candidates[row["id"]] = row

    conn.close()

    results = []

    # * ---------------------------------------
    # * Rank Candidates
    # * ---------------------------------------

    for row in candidates.values():

        memory = row_to_memory(row)
        
        score = score_memory(memory, keywords)

        if score >= MIN_SCORE:

            results.append((score, memory))

    results.sort(

        key=lambda x: x[0],

        reverse=True

    )
    
    # * -----------------------
    # * Final Ranking
    # * -----------------------

    ranked = rank(

        [memory for _, memory in results]

    )

    results = [

        (0, memory)

        for memory in ranked

    ]

    final = []

    for score, memory in results[:limit]:

        touch(memory.key)

        # * -----------------------
        # * Confidence Score
        # * -----------------------

        info = confidence(

            memory.key,

            memory.value

        )

        memory.confidence = info["score"]

        final.append(memory)

    return final


# * ---------------------------------------
# * Search by Category
# * ---------------------------------------

def search_category(

    category,

    limit=10

):

    conn = connect()

    cursor = conn.cursor()

    cursor.execute(

        """

        SELECT *

        FROM memories

        WHERE category=?

        ORDER BY importance DESC

        LIMIT ?

        """,

        (

            category,

            limit

        )

    )

    rows = cursor.fetchall()

    conn.close()

    memories = []

    for row in rows:

        memories.append(
            row_to_memory(row)
        )

    return memories


# * ---------------------------------------
# * Format Memories
# * ---------------------------------------

def format_memories(memories):

    if not memories:

        return ""

    text = ""

    for memory in memories:

        text += (

            f"{memory.key}: "

            f"{memory.value}\n"

        )

    return text

def row_to_memory(row):

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