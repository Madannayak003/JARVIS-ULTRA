PENDING_CONFIRMATION = None


def ask(action, data):
    global PENDING_CONFIRMATION

    PENDING_CONFIRMATION = data.copy()
    PENDING_CONFIRMATION["action"] = action


def get():
    return PENDING_CONFIRMATION


def clear():
    global PENDING_CONFIRMATION

    PENDING_CONFIRMATION = None


def waiting():
    return PENDING_CONFIRMATION is not None