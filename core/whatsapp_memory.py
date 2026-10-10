_pending_contact = None
_pending_message = None


def set_contact(contact):
    global _pending_contact
    _pending_contact = contact


def get_contact():
    return _pending_contact


def clear_contact():
    global _pending_contact
    _pending_contact = None


# * -------------------------
# * Waiting for Contact
# * -------------------------

def set_pending_message(message=""):
    global _pending_message
    _pending_message = message


def get_pending_message():
    return _pending_message


def clear_pending_message():
    global _pending_message
    _pending_message = None