"""
JARVIS PRO HUD
Event Bus
"""

import threading

from .events import HUDEvent


class HUDEventBus:

    def __init__(self):

        self._listeners = []

        self._lock = threading.Lock()

    # * --------------------------------------------------

    def subscribe(self, callback):

        if callback is None:
            return

        with self._lock:

            if callback not in self._listeners:

                self._listeners.append(
                    callback
                )

    # * --------------------------------------------------

    def unsubscribe(self, callback):

        with self._lock:

            if callback in self._listeners:

                self._listeners.remove(
                    callback
                )

    # * --------------------------------------------------

    def publish(self, event: HUDEvent):

        with self._lock:

            listeners = list(
                self._listeners
            )

        for callback in listeners:

            try:

                callback(event)

            except Exception as exc:

                print(
                    "[HUD BUS] Listener error:",
                    exc
                )


hud_bus = HUDEventBus()