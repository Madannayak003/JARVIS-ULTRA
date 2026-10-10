import threading


_core_ready = threading.Event()


def mark_core_ready():
    _core_ready.set()


def wait_for_core():
    _core_ready.wait()


def is_core_ready():
    return _core_ready.is_set()
