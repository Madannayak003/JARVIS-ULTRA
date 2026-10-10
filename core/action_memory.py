"""
Action Memory

Stores the last actions performed by JARVIS.
"""

_memory = {
    "app": None,
    "site": None,
    "search": None,
    "action": None,
    "media": None,
    "folder": None,
    "file": None,

    # * Search preference
    "search_platform": None,

    # * Legacy (will remove later)
    "pending_subject": None,

    # * NEW
    "clarify_context": None
}


def set_memory(key, value):

    _memory[key] = value


def get_memory(key):

    return _memory.get(key)


def clear_memory():

    for key in _memory:

        _memory[key] = None


def dump():

    return _memory.copy()