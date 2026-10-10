"""
JARVIS PRO
Memory Pipeline

Stage 2B

Responsibilities
----------------
✓ Central memory learning pipeline
✓ Try rule-based learning first
✓ Fall back to AI learning
✓ Save memories
✓ Return a unified result
"""

from ai.memory_manager import learn as rule_learn
from ai.memory_ai import extract_memory
from ai.memory_preference import extract as extract_preference
from ai.memory_confidence import confidence
from ai.memory_store import remember, get


# * ---------------------------------------
# * Learn
# * ---------------------------------------

def learn(text):

    # * -------------------------------
    # * Stage 1
    # * Rule-based learning
    # * -------------------------------

    result = rule_learn(text)

    if result.get("saved"):

        result["source"] = "rules"

        return result

    if result.get("already_known"):

        result["source"] = "rules"

        return result

    # * -------------------------------
    # * Stage 2
    # * Skip Questions
    # * -------------------------------

    question_words = (
        "what",
        "who",
        "where",
        "when",
        "why",
        "how",
        "which",
        "do",
        "does",
        "did",
        "can",
        "could",
        "will",
        "would",
        "is",
        "are"
    )

    text_lower = text.lower().strip()

    if (
        text_lower.endswith("?")
        or text_lower.startswith(question_words)
    ):
        return {
            "saved": False
        }

    # * -------------------------------
    # AI / Preference Learning
    # * -------------------------------

    data = extract_memory(text)

    # * -------------------------------
    # * Preference Learning
    # * -------------------------------

    if (

        not data

        or not data.get("remember")

    ):

        data = extract_preference(text)

    if not data:

        return {

            "saved": False

        }

    if not data.get("remember"):

        return {

            "saved": False

        }

    if not data:

        return {"saved": False}

    if not data.get("remember"):

        return {"saved": False}

    key = data["key"]

    value = data["value"]

    existing = get(key)
    
    # * -------------------------------
    # * Confidence
    # * -------------------------------

    info = confidence(

        key,

        value

    )

    print(

        f"[MEMORY CONFIDENCE] "

        f"{info['score']} "

        f"({info['status']})"

    )

    # * -------------------------------
    # * Already Known
    # * -------------------------------

    if existing:

        if existing.value.lower() == value.lower():

            return {

                "saved": False,

                "already_known": True,

                "memory": existing,

                "source": "ai"

            }

    updated = False

    old_value = None

    if existing:

        updated = True

        old_value = existing.value

    # * -------------------------------
    # * Save Memory
    # * -------------------------------

    remember(

        key=key,

        value=value,

        category=data.get("category", "other"),

        keywords=data.get("keywords", ""),

        importance=data.get("importance", 2)

    )

    print(

        f"[MEMORY AI] Saved -> "

        f"{key} = {value}"

    )

    return {

        "saved": True,

        "updated": updated,

        "already_known": False,

        "old_value": old_value,

        "key": key,

        "value": value,

        "category": data.get("category"),

        "importance": data.get("importance"),
        
        "confidence": info["score"],

        "source": "ai"

    }