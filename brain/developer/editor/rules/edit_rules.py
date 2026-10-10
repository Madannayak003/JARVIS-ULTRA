"""
JARVIS PRO
Developer Editor

Editor Rules
"""

# * ==================================================
# * Supported Edit Actions
# * ==================================================

SUPPORTED_ACTIONS = {

    "ADD",
    "REMOVE",
    "UPDATE",
    "MODIFY",
    "FIX",
    "REPLACE",
    "RENAME",
    "REFACTOR",
    "OPTIMIZE",
    "FORMAT",

}

# * ==================================================
# * Prompt Limits
# * ==================================================

MAX_PROMPT_CHARACTERS = 50000

MAX_FILES_PER_REQUEST = 10

FULL_FILE_LIMIT = 300

# * ==================================================
# * Target Selection
# * ==================================================

MAX_TARGET_FILES = 5

# * ==================================================
# * Workspace
# * ==================================================

CREATE_BACKUP = True

VALIDATE_PATCHES = True

ALLOW_NEW_FILES = True

ALLOW_DELETE_FILES = False

ALLOW_OVERWRITE = True

# * ==================================================
# * Generator
# * ==================================================

GENERATION_TIMEOUT = 120

MAX_RETRIES = 1

# * ==================================================
# * Supported Extensions
# * ==================================================

SUPPORTED_EXTENSIONS = {

    ".py",
    ".ino",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".html",
    ".css",
    ".js",
    ".ts",
    ".json",
    ".xml",
    ".yaml",
    ".yml",
    ".md",

}