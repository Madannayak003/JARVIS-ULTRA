# * Current conversation context

_context = {
    "last_app": None,
    "last_website": None,
    "last_contact": None,
    "last_song": None,
    "last_file": None,
    "last_command": None,
}

def set_context(key, value):
    _context[key] = value


def get_context(key):
    return _context.get(key)


def clear_context():
    global _context

    _context = {
        "last_app": None,
        "last_website": None,
        "last_contact": None,
        "last_song": None,
        "last_file": None,
        "last_command": None,
    }


def all_context():
    return _context