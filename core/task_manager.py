"""
JARVIS Runtime Manager

Responsible for:

- AI Chat
- Planner
- Browser
- Vision
- Camera
- Downloads

Only ONE task of each type runs at a time.
"""

import threading
from core.diagnostics import debug_print


class TaskManager:

    def __init__(self):
        self.tasks = {}
        self.stop_events = {}
        self.lock = threading.Lock()

    def start(self, name, target, *args):

        with self.lock:

            # * Stop previous task of same type
            self.stop(name)

            stop_event = threading.Event()

            self.stop_events[name] = stop_event

            thread = threading.Thread(
                target=target,
                args=(*args, stop_event),
                daemon=True
            )

            self.tasks[name] = thread

            thread.start()

            debug_print(f"[TASK] Started : {name}")

    def stop(self, name):

        thread = self.tasks.get(name)
        event = self.stop_events.get(name)

        if thread and thread.is_alive():

            debug_print(f"[TASK] Stopping : {name}")

            event.set()

        self.tasks.pop(name, None)
        self.stop_events.pop(name, None)

    def stop_all(self):

        for name in list(self.tasks.keys()):
            self.stop(name)

    def running(self, name):

        thread = self.tasks.get(name)

        return thread is not None and thread.is_alive()

    def event(self, name):
        return self.stop_events.get(name)


task_manager = TaskManager()
