"""
JARVIS PRO
Memory Schema V2

Central place for all memory constants.

Every other memory module imports from here.
"""

from dataclasses import dataclass
from datetime import datetime


# * ---------------------------------------
# * Memory Categories
# * ---------------------------------------

PERSONAL = "personal"

PROJECT = "project"

WORK = "work"

EDUCATION = "education"

PREFERENCE = "preference"

CONTACT = "contact"

SYSTEM = "system"

OTHER = "other"


# * ---------------------------------------
# * Importance
# * ---------------------------------------

LOW = 1

MEDIUM = 2

HIGH = 3

CRITICAL = 4


# * ---------------------------------------
# * Memory Record
# * ---------------------------------------

@dataclass
class Memory:

    id: int | None = None

    key: str = ""

    value: str = ""

    category: str = OTHER

    keywords: str = ""

    importance: int = MEDIUM

    created_at: str = ""

    updated_at: str = ""

    last_used: str = ""

    use_count: int = 0


# * ---------------------------------------
# * Timestamp Helper
# * ---------------------------------------

def now():

    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )