from queue import Queue

VOICE_QUEUE = Queue()


def add(text):

    VOICE_QUEUE.put(text)


def get():

    return VOICE_QUEUE.get()


def empty():

    return VOICE_QUEUE.empty()