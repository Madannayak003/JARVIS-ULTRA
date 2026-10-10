from queue import Queue
import uuid

TASK_QUEUE = Queue()

def add_task(task):
    
    task["id"] = str(uuid.uuid4())[:8]
    TASK_QUEUE.put(task)


def get_task():

    if TASK_QUEUE.empty():
        return None

    return TASK_QUEUE.get()


def has_tasks():

    return not TASK_QUEUE.empty()


def clear():

    while not TASK_QUEUE.empty():
        TASK_QUEUE.get()
        
def size():

    return TASK_QUEUE.qsize()