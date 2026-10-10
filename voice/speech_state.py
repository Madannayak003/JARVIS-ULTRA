import threading

_speaking = False
_lock = threading.Lock()


def set_speaking(value: bool):
    global _speaking

    with _lock:
        _speaking = bool(value)


def is_speaking():
    with _lock:
        return _speaking