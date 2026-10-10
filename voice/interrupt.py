import threading

STOP_EVENT = threading.Event()


def stop():

    STOP_EVENT.set()


def clear():

    STOP_EVENT.clear()


def stopped():

    return STOP_EVENT.is_set()