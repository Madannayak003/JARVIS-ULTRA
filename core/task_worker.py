import threading
import time

from core.task_queue import get_task
from core.task_queue import has_tasks

from core.registry import execute
from core.diagnostics import debug_print

running = True

def worker():

    while running:

        if has_tasks():

            task = get_task()

            action = task["action"]

            debug_print("[TASK] Starting:", action)

            execute(action, task)

            debug_print("[TASK] Finished:", action)

        else:

            time.sleep(0.1)


def start_worker():

    threading.Thread(
        target=worker,
        daemon=True
    ).start()
