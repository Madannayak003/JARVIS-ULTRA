"""
JARVIS PRO
Developer Analyzer

Intent Rules
"""

from brain.developer.enums import Intent


INTENT_RULES = {

    Intent.CREATE: [
        "create",
        "make",
        "build",
        "generate",
        "develop",
        "write",
        "start",
        "new",
    ],

    Intent.EDIT: [
        "edit",
        "modify",
        "change",
        "rewrite",
        "refactor",
        "improve",
    ],

    Intent.UPDATE: [
        "update",
        "upgrade",
        "add",
        "extend",
        "append",
    ],

    Intent.FIX: [
        "fix",
        "repair",
        "solve",
        "debug",
        "correct",
        "resolve",
    ],

    Intent.DELETE: [
        "delete",
        "remove",
        "erase",
        "clear",
    ],

    Intent.EXPLAIN: [
        "explain",
        "describe",
        "teach",
        "what",
        "why",
        "how",
    ],

    Intent.ANALYZE: [
        "analyze",
        "analyse",
        "review",
        "inspect",
        "check",
        "evaluate",
    ],
}