"""
Developer Intent
"""

from enum import Enum


class Intent(str, Enum):
    CREATE = "create"
    EDIT = "edit"
    UPDATE = "update"
    FIX = "fix"
    DELETE = "delete"
    EXPLAIN = "explain"
    ANALYZE = "analyze"
    UNKNOWN = "unknown"