"""
JARVIS PRO
Semantic Memory

Stage 3A

Responsibilities
----------------
✓ Semantic memory lookup
✓ Related word matching
✓ Ranking
✓ Better retrieval
"""

from ai.memory_store import list_all


# * ---------------------------------------
# * Semantic Vocabulary
# * ---------------------------------------

VOCABULARY = {

    "name": {
        "name",
        "who",
        "identity",
        "myself",
        "full name"
    },

    "college": {
        "college",
        "study",
        "studying",
        "university",
        "campus",
        "education",
        "school"
    },

    "project": {
        "project",
        "working",
        "build",
        "building",
        "developing"
    },

    "email": {
        "email",
        "mail",
        "gmail",
        "address"
    },

    "phone": {
        "phone",
        "mobile",
        "number",
        "contact"
    },

    "birthday": {
        "birthday",
        "birth",
        "dob",
        "born"
    },

    "favorite_language": {
        "language",
        "python",
        "programming",
        "coding"
    },

    "os": {
        "windows",
        "linux",
        "ubuntu",
        "operating",
        "system",
        "os"
    },

    "laptop_brand": {
        "laptop",
        "computer",
        "pc",
        "notebook"
    }

}


# * ---------------------------------------
# * Tokenize
# * ---------------------------------------

def tokenize(text):

    return {

        word.strip(".,?!").lower()

        for word in text.split()

    }


# * ---------------------------------------
# * Semantic Search
# * ---------------------------------------

def search(question):

    words = tokenize(question)

    best_memory = None

    best_score = 0

    for memory in list_all():

        vocab = VOCABULARY.get(

            memory.key,

            {memory.key}

        )

        score = len(

            words & vocab

        )

        if score > best_score:

            best_score = score

            best_memory = memory

    return best_memory