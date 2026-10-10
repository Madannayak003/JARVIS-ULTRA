"""
JARVIS PRO
Battery Skill

Provides current battery information and automatic
low-battery monitoring.
"""

import threading
import time

import psutil

from core.registry import register
from voice.manager import speak


# * =========================================================
# * Configuration
# * =========================================================

LOW_BATTERY_THRESHOLD = 30
RESET_BATTERY_THRESHOLD = 35
MONITOR_INTERVAL = 60


# * =========================================================
# * Monitor State
# * =========================================================

_monitor_started = False
_low_battery_alerted = False
_monitor_lock = threading.Lock()


# * =========================================================
# * Battery
# * =========================================================

def battery(data=None):
    """
    Report the current battery level.

    Supports the normal registry interface:

        battery(data)

    Natural-language interpretation happens before this
    skill is called, keeping execution fast.
    """

    try:

        info = psutil.sensors_battery()

        # * -------------------------------------------------
        # * Battery unavailable
        # * -------------------------------------------------

        if info is None:

            speak(
                "I can't access the battery information right now."
            )

            return False

        percent = int(round(info.percent))
        plugged = bool(info.power_plugged)

        # * -------------------------------------------------
        # * Charging
        # * -------------------------------------------------

        if plugged:

            if percent >= 100:

                message = (
                    "Your battery is fully charged."
                )

            else:

                message = (
                    f"You're at {percent} percent, "
                    "and the charger is connected."
                )

        # * -------------------------------------------------
        # * Not charging
        # * -------------------------------------------------

        else:

            if percent <= 10:

                message = (
                    f"You're at {percent} percent. "
                    "Your battery is getting very low."
                )

            elif percent <= 20:

                message = (
                    f"You're at {percent} percent. "
                    "You may want to charge soon."
                )

            elif percent <= LOW_BATTERY_THRESHOLD:

                message = (
                    f"You're at {percent} percent. "
                    "Please connect the charger soon."
                )

            else:

                message = (
                    f"You're at {percent} percent."
                )

        # * -------------------------------------------------
        # * Speak
        # * -------------------------------------------------

        speak(message)

        # * -------------------------------------------------
        # ! Debug
        # * -------------------------------------------------

        print(
            f"[BATTERY] {percent}% | "
            f"Plugged: {plugged}"
        )

        return True

    except Exception as e:

        print(
            f"[BATTERY ERROR] {e}"
        )

        speak(
            "I couldn't check the battery level."
        )

        return False


# * =========================================================
# * Automatic Battery Monitor
# * =========================================================

def _battery_monitor():

    global _low_battery_alerted

    print(
        "[BATTERY] Automatic monitor started"
    )

    while True:

        try:

            info = psutil.sensors_battery()

            if info is None:

                time.sleep(MONITOR_INTERVAL)

                continue

            percent = int(round(info.percent))
            plugged = bool(info.power_plugged)

            # * -------------------------------------------------
            # * Charger connected
            # * -------------------------------------------------

            if plugged:

                if _low_battery_alerted:

                    print(
                        "[BATTERY] Charger connected - "
                        "low battery alert reset"
                    )

                _low_battery_alerted = False

            # * -------------------------------------------------
            # * Battery recovered
            # * -------------------------------------------------

            elif percent >= RESET_BATTERY_THRESHOLD:

                _low_battery_alerted = False

            # * -------------------------------------------------
            # * Automatic low battery alert
            # * -------------------------------------------------

            elif (
                percent <= LOW_BATTERY_THRESHOLD
                and not _low_battery_alerted
            ):

                speak(
                    f"Sir, your battery is at "
                    f"{percent} percent. "
                    "Please connect the charger."
                )

                _low_battery_alerted = True

                print(
                    f"[BATTERY] LOW BATTERY ALERT: "
                    f"{percent}%"
                )

        except Exception as e:

            print(
                f"[BATTERY MONITOR ERROR] {e}"
            )

        time.sleep(MONITOR_INTERVAL)


# * =========================================================
# * Start Automatic Monitor
# * =========================================================

def start_battery_monitor():

    global _monitor_started

    with _monitor_lock:

        if _monitor_started:

            return

        _monitor_started = True

        thread = threading.Thread(
            target=_battery_monitor,
            daemon=True,
            name="BatteryMonitor",
        )

        thread.start()


# * =========================================================
# * Registry
# * =========================================================

register(
    "battery",
    battery,
)


# * =========================================================
# * Start Monitor
# * =========================================================

start_battery_monitor()