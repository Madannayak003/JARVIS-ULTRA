"""
JARVIS PRO HUD
System Telemetry
"""

import time

try:

    import psutil

except ImportError:

    psutil = None


class HUDTelemetry:

    def cpu(self):

        if psutil is None:
            return None

        try:

            return round(
                psutil.cpu_percent(
                    interval=None
                ),
                1
            )

        except Exception:

            return None

    # * --------------------------------------------------

    def ram(self):

        if psutil is None:
            return None

        try:

            return round(
                psutil.virtual_memory().percent,
                1
            )

        except Exception:

            return None

    # * --------------------------------------------------

    def battery(self):

        if psutil is None:
            return None

        try:

            battery = psutil.sensors_battery()

            if battery is None:
                return None

            return round(
                battery.percent,
                1
            )

        except Exception:

            return None
        
    # * --------------------------------------------------

    def available(self):

        return psutil is not None

    # * --------------------------------------------------

    def read(self):

        return {

            "cpu": self.cpu(),

            "ram": self.ram(),

            "battery": self.battery(),

            "timestamp": time.time(),

        }


telemetry = HUDTelemetry()