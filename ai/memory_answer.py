"""
JARVIS PRO
Memory Answer Engine

Responsibilities

✓ Instant personal memory answers
✓ Direct memory lookup
✓ Alias-based lookup
✓ Key-based lookup
✓ Keyword-based lookup
✓ Semantic fallback
✓ Safe confidence filtering
✓ No Ollama required
"""

import re

from ai.memory_store import (
    get,
    all_memories,
)

from ai.memory_search import (
    search,
)

from ai.memory_profile import (
    profile_summary,
)


# * =========================================================
# * Question Aliases
# * =========================================================

QUESTION_ALIASES = {

    # * -----------------------------------------------------
    # * Identity
    # * -----------------------------------------------------

    "name": [
        "name",
        "who am i",
        "full name",
        "myself",
        "identity",
    ],

    # * -----------------------------------------------------
    # * Education
    # * -----------------------------------------------------

    "college": [
        "college",
        "study",
        "university",
        "institution",
        "campus",
    ],

    # * -----------------------------------------------------
    # * Project
    # * -----------------------------------------------------

    "project": [
        "project",
        "working on",
        "final year project",
        "current project",
    ],

    # * -----------------------------------------------------
    # * Birthday
    # * -----------------------------------------------------

    "birthday": [
        "birthday",
        "birth date",
        "date of birth",
        "dob",
    ],

    # * -----------------------------------------------------
    # * Contact
    # * -----------------------------------------------------

    "phone": [
        "phone",
        "mobile",
        "phone number",
        "mobile number",
        "contact number",
        "contact",
    ],

    "email": [
        "email",
        "mail",
        "gmail",
        "email address",
    ],

    # * -----------------------------------------------------
    # * Programming
    # * -----------------------------------------------------

    "favorite_language": [
        "favorite language",
        "favourite language",
        "programming language",
        "coding language",
    ],

    # * -----------------------------------------------------
    # * Bike
    # * -----------------------------------------------------

    "bike": [
        "bike",
        "my bike",
        "which bike",
        "what bike",
        "motorcycle",
        "motorbike",
        "which motorcycle",
        "what motorcycle",
        "vehicle i have",
        "vehicle i own",
    ],

    # * -----------------------------------------------------
    # * Dream Bike
    # * -----------------------------------------------------

    "dream_bike": [
        "dream bike",
        "dreambike",
        "dream motorcycle",
        "dream motorbike",
        "dream vehicle",
    ],

    # * -----------------------------------------------------
    # * Computer
    # * -----------------------------------------------------

    "os": [
        "operating system",
        "windows",
        "os",
    ],

    "laptop_brand": [
        "laptop",
        "computer",
        "pc",
        "laptop brand",
    ],

    "preferred_browser": [
        "browser",
        "chrome",
        "firefox",
        "preferred browser",
    ],

    "preferred_editor": [
        "editor",
        "vs code",
        "vscode",
        "ide",
        "preferred editor",
    ],

    "preferred_theme": [
        "theme",
        "dark mode",
        "light mode",
        "preferred theme",
    ],

    # * -----------------------------------------------------
    # * Other known memories
    # * -----------------------------------------------------

    "favorite_drink": [
        "favorite drink",
        "favourite drink",
        "drink",
    ],

    "github": [
        "github",
        "github username",
        "github id",
    ],

    "city": [
        "city",
        "where do i live",
        "where i live",
        "location",
    ],
}


# * =========================================================
# * Response Templates
# * =========================================================

RESPONSES = {

    "name":
        "Your name is {value}.",

    "college":
        "You study at {value}.",

    "project":
        "Your project is {value}.",

    "birthday":
        "Your date of birth is {value}.",

    "phone":
        "Your phone number is {value}.",

    "email":
        "Your email address is {value}.",

    "favorite_language":
        "Your favorite programming language is {value}.",

    "bike":
        "You have a {value} bike.",

    "dream_bike":
        "Your dream bike is {value}.",

    "os":
        "You use {value}.",

    "laptop_brand":
        "Your laptop is {value}.",

    "preferred_browser":
        "Your preferred browser is {value}.",

    "preferred_editor":
        "Your preferred editor is {value}.",

    "preferred_theme":
        "You prefer {value}.",

    "favorite_drink":
        "Your favorite drink is {value}.",

    "github":
        "Your GitHub username is {value}.",

    "city":
        "You live in {value}.",
}


# * =========================================================
# * Personal Question Detector
# * =========================================================

PERSONAL_PATTERNS = [

    r"\bmy\b",
    r"\bme\b",
    r"\bmine\b",

    r"\bwho am i\b",

    r"\bwhat is my\b",
    r"\bwhat's my\b",

    r"\bwhere do i\b",
    r"\bwhere am i\b",

    r"\bwhich\b.*\bdo i\b",
    r"\bwhich\b.*\bmy\b",

    r"\bwhat\b.*\bdo i\b",
    r"\bwhat\b.*\bmy\b",

    r"\bdo i\b",
    r"\bdid i\b",

    r"\bi study\b",
    r"\bi work\b",
    r"\bi live\b",

]


def is_personal_question(question):

    question = question.lower().strip()

    for pattern in PERSONAL_PATTERNS:

        if re.search(
            pattern,
            question,
        ):

            return True

    return False


# * =========================================================
# * Normalize Text
# * =========================================================

def _normalize_text(text):

    if not text:

        return ""

    text = str(text).lower().strip()

    text = re.sub(
        r"[^\w\s+#.-]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# * =========================================================
# * Normalize Question
# * =========================================================

def normalize_question(question):

    question = _normalize_text(
        question
    )

    # * -----------------------------------------------------
    # * Longest aliases first
    #
    # * Prevent:
    #
    # * "dream bike"
    #
    # * from being interpreted as:
    #
    # * "bike"
    # * -----------------------------------------------------

    aliases = []

    for key, values in QUESTION_ALIASES.items():

        for alias in values:

            aliases.append(
                (
                    key,
                    _normalize_text(alias),
                )
            )

    aliases.sort(
        key=lambda item: len(item[1]),
        reverse=True,
    )

    for key, alias in aliases:

        if alias and alias in question:

            return key

    return None


# * =========================================================
# * Safe Memory Lookup
# * =========================================================

def _get_memory(key):

    if not key:

        return None

    try:

        return get(key)

    except Exception as exc:

        print(
            "[MEMORY ANSWER] Lookup error:",
            exc,
        )

        return None


# * =========================================================
# * Format Memory
# * =========================================================

def _format_memory(memory):

    if not memory:

        return None

    key = memory.key

    value = memory.value

    template = RESPONSES.get(
        key
    )

    if template:

        return template.format(
            value=value
        )

    return str(value)


# * =========================================================
# * Direct Alias Answer
# * =========================================================

def direct_answer(question):

    normalized = _normalize_text(
        question
    )

    if not normalized:

        return None

    # * -----------------------------------------------------
    # * First: explicit alias
    # * -----------------------------------------------------

    key = normalize_question(
        normalized
    )

    if key:

        memory = _get_memory(
            key
        )

        if memory:

            return _format_memory(
                memory
            )

    # * -----------------------------------------------------
    # * Second: direct key matching
    # * -----------------------------------------------------

    try:

        memories = all_memories()

    except Exception as exc:

        print(
            "[MEMORY ANSWER] "
            "Could not load memories:",
            exc,
        )

        memories = []

    # * -----------------------------------------------------
    # * Score memories
    # * -----------------------------------------------------

    candidates = []

    question_words = set(
        normalized.split()
    )

    for memory in memories:

        memory_key = _normalize_text(
            memory.key
        )

        memory_keywords = _normalize_text(
            memory.keywords
        )

        # * -----------------------------------------------
        # ! Do not confuse dream_bike with bike
        # * -----------------------------------------------

        score = 0

        # * -----------------------------------------------
        # * Exact key
        # * -----------------------------------------------

        if memory_key in normalized:

            score += 100

        # * -----------------------------------------------
        # * Alias matching
        # * -----------------------------------------------

        aliases = QUESTION_ALIASES.get(
            memory.key,
            [],
        )

        for alias in aliases:

            alias = _normalize_text(
                alias
            )

            if alias and alias in normalized:

                score += 80

        # * -----------------------------------------------
        # * Keyword matching
        # * -----------------------------------------------

        for keyword in memory_keywords.split():

            if keyword in question_words:

                score += 15

        # * -----------------------------------------------
        # * Key token matching
        # * -----------------------------------------------

        for token in re.split(
            r"[_\s-]+",
            memory_key,
        ):

            if (
                token
                and token in question_words
            ):

                score += 10

        if score > 0:

            candidates.append(
                (
                    score,
                    memory,
                )
            )

    # * -----------------------------------------------------
    # * Best deterministic result
    # * -----------------------------------------------------

    if candidates:

        candidates.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        best_score, best_memory = (
            candidates[0]
        )

        # * -----------------------------------------------
        # * Require reasonable confidence
        # * -----------------------------------------------

        if best_score >= 20:

            return _format_memory(
                best_memory
            )

    # * -----------------------------------------------------
    # * Semantic fallback
    # * -----------------------------------------------------

    try:

        memories = search(
            question,
            limit=3,
        )

    except Exception as exc:

        print(
            "[MEMORY ANSWER] "
            "Semantic search error:",
            exc,
        )

        memories = []

    if memories:

        # * -----------------------------------------------
        # * Prefer a known response template
        # * -----------------------------------------------

        for memory in memories:

            if memory.key in RESPONSES:

                return _format_memory(
                    memory
                )

        # * -----------------------------------------------
        # * Generic memory
        # * -----------------------------------------------

        memory = memories[0]

        if memory:

            return _format_memory(
                memory
            )

    return None


# * =========================================================
# * Public API
# * =========================================================

def answer(question):

    if not question:

        return None

    # * -----------------------------------------------------
    # * Personal question check
    # * -----------------------------------------------------

    if not is_personal_question(
        question
    ):

        return None

    question = _normalize_text(
        question
    )

    # * -----------------------------------------------------
    # * Profile Requests
    # * -----------------------------------------------------

    if (

        "profile" in question

        or "everything about me" in question

        or "what do you know about me" in question

    ):

        return profile_summary()

    # * -----------------------------------------------------
    # * Memory Lookup
    # * -----------------------------------------------------

    return direct_answer(
        question
    )