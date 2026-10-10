"""
JARVIS PRO
HUD Runtime

Owns the HUD runtime lifecycle.

The runtime provides background HUD services such as
system telemetry.

IMPORTANT:
This module does NOT control JARVIS.
It only publishes display information to the HUD.
"""

from __future__ import annotations

import threading
from core.diagnostics import debug_print
import time

from .manager import hud
from .telemetry import telemetry


class HUDRuntime:

    TELEMETRY_INTERVAL = 1.0

    def __init__(self):

        self.running = False

        self.thread: threading.Thread | None = None

        self._stop_event = threading.Event()

        self._started_at = time.monotonic()

    # * =====================================================
    # * Start
    # * =====================================================

    def start(self):

        if self.running:

            return

        self.running = True

        self._stop_event.clear()

        self.thread = threading.Thread(

            target=self._run,

            name="jarvis-hud-runtime",

            daemon=True,

        )

        self.thread.start()

        debug_print(
            "[HUD RUNTIME] Started."
        )

    # * =====================================================
    # * Stop
    # * =====================================================

    def stop(self):

        if not self.running:

            return

        self.running = False

        self._stop_event.set()

        thread = self.thread

        if thread is not None and thread.is_alive():

            thread.join(
                timeout=2.0
            )

        self.thread = None

        debug_print(
            "[HUD RUNTIME] Stopped."
        )

    # * =====================================================
    # * Runtime Loop
    # * =====================================================

    def _run(self):

        while not self._stop_event.is_set():

            try:

                self._update_telemetry()

            except Exception as exc:

                print(
                    "[HUD RUNTIME] Telemetry error:",
                    exc
                )

            self._stop_event.wait(
                self.TELEMETRY_INTERVAL
            )

    # * =====================================================
    # * Telemetry
    # * =====================================================

    def _update_telemetry(self):

        data = (
            telemetry.read()
            if telemetry.available()
            else {"timestamp": time.time()}
        )

        if not isinstance(data, dict):

            return

        data["uptime"] = self.uptime()

        hud.system_update(
            data
        )

    # * =====================================================
    # * Status
    # * =====================================================

    def uptime(self):

        return max(
            0,
            time.monotonic() - self._started_at
        )

    # * =====================================================

    def is_running(self):

        return self.running


# * =========================================================
# * Singleton
# * =========================================================

hud_runtime = HUDRuntime()
