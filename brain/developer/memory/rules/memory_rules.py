"""
JARVIS PRO
Developer Memory

Memory Rules
"""

# * ==================================================
# * Memory Categories
# * ==================================================

MEMORY_CATEGORIES = {

    "PROJECT",
    "FILE",
    "SYMBOL",
    "DEPENDENCY",
    "STYLE",
    "EDIT",
    "SESSION",

}


# * ==================================================
# * Storage
# * ==================================================

MEMORY_DIRECTORY = ".jarvis_memory"

MEMORY_FILE = "memory.json"

MEMORY_VERSION = 1


# * ==================================================
# * Limits
# * ==================================================

MAX_MEMORY_RECORDS = 1000

MAX_EDIT_HISTORY = 100

MAX_RECENT_REQUESTS = 20

MAX_RECENT_FILES = 20

MAX_SEARCH_RESULTS = 10


# * ==================================================
# * Memory Behavior
# * ==================================================

AUTO_SAVE = True

AUTO_LOAD = True

TRACK_FILE_CHANGES = True

TRACK_EDIT_HISTORY = True

TRACK_STYLE = True

TRACK_DEPENDENCIES = True


# * ==================================================
# * Search
# * ==================================================

MIN_SEARCH_SCORE = 1

CASE_SENSITIVE_SEARCH = False


# * ==================================================
# * Safety
# * ==================================================

IGNORE_DIRECTORIES = {

    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".jarvis_memory",
    ".jarvis_backups",
    "node_modules",

}


IGNORE_FILES = {

    ".env",
    ".env.local",

}


# * ==================================================
# * Supported File Extensions
# * ==================================================

MEMORY_EXTENSIONS = {

    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".ino",
    ".java",
    ".html",
    ".css",
    ".json",
    ".xml",
    ".yaml",
    ".yml",
    ".md",

}