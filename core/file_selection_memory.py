_pending = None


def set_files(data):

    global _pending

    _pending = data


def get_files():

    return _pending


def clear_files():

    global _pending

    _pending = None