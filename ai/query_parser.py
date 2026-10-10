"""
JARVIS PRO
Query Parser

Responsibilities
----------------
✓ Normalize text
✓ Remove stop words
✓ Extract keywords
✓ Expand synonyms
"""

import re


# * ---------------------------------------
# * Stop Words
# * ---------------------------------------

STOP_WORDS = {

    "what",
    "who",
    "where",
    "when",
    "why",
    "how",

    "is",
    "are",
    "am",
    "was",
    "were",
    "be",
    "been",

    "i",
    "im",
    "i'm",
    "me",
    "my",
    "myself",
    "your",
    "you",

    "the",
    "a",
    "an",

    "tell",
    "about",

    "do",
    "does",
    "did",

    "can",
    "could",
    "would",
    "will",

    "to",
    "of",
    "for",
    "and",
    "or",
    "on",
    "in",
    "at",
    "with",
    "from"
}


# * ---------------------------------------
# * Synonyms
# * ---------------------------------------

SYNONYMS = {

    "who am i": [

        "name",
        "identity",
        "user"

    ],

    "myself": [

        "name",
        "identity"

    ],

    "college name": [

        "college"

    ],

    "project": [

        "project"

    ],

    "home": [

        "address"

    ],

    "phone": [

        "mobile"

    ]

}


# * ---------------------------------------
# * Normalize
# * ---------------------------------------

def normalize(text):

    text = text.lower()

    text = re.sub(

        r"[^\w\s]",

        "",

        text

    )

    return text.strip()


# * ---------------------------------------
# * Extract Keywords
# * ---------------------------------------

def extract_keywords(query):

    query = normalize(query)

    keywords = []

    # * Phrase Synonyms

    for phrase, words in SYNONYMS.items():

        if phrase in query:

            keywords.extend(words)

    # * Single Words

    for word in query.split():

        if word not in STOP_WORDS:

            keywords.append(word)

    # * Remove duplicates

    seen = set()

    result = []

    for word in keywords:

        if word not in seen:

            seen.add(word)

            result.append(word)

    return result