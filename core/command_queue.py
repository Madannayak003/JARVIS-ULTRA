"""
Command Queue

Executes commands sequentially.
"""

from queue import Queue


_queue = Queue()


def put(command):
    _queue.put(command)


def get():
    return _queue.get()


def empty():
    return _queue.empty()


def clear():

    while not _queue.empty():

        try:
            _queue.get_nowait()

        except:
            break


def size():
    return _queue.qsize()