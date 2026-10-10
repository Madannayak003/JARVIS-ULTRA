"""
JARVIS PRO
Task Manager Skill

Provides quick system performance information:
CPU, RAM and Disk usage.
"""

import psutil

from core.registry import register
from voice.manager import speak


# * =========================================================
# * Task Manager / System Status
# * =========================================================

def taskmanager(data=None):
    """
    Report current CPU, RAM and Disk usage.

    Registry action:
        taskmanager
    """

    try:

        # * -------------------------------------------------
        # * CPU
        # * -------------------------------------------------

        cpu = psutil.cpu_percent(interval=0.2)

        # * -------------------------------------------------
        # * RAM
        # * -------------------------------------------------

        ram = psutil.virtual_memory().percent

        # * -------------------------------------------------
        # * Disk
        # * -------------------------------------------------

        disk = psutil.disk_usage("C:\\").percent

        cpu = int(round(cpu))
        ram = int(round(ram))
        disk = int(round(disk))

        # * -------------------------------------------------
        # * Terminal diagnostics
        # * -------------------------------------------------

        print()
        print("========== SYSTEM STATUS ==========")
        print(f"CPU  : {cpu}%")
        print(f"RAM  : {ram}%")
        print(f"Disk : {disk}%")
        print("===================================")
        print()

        # * -------------------------------------------------
        # * Natural response
        # * -------------------------------------------------

        speak(
            f"Your CPU is at {cpu} percent, "
            f"memory usage is {ram} percent, "
            f"and disk usage is {disk} percent."
        )

        print(
            f"[TASKMANAGER] CPU {cpu}% | "
            f"RAM {ram}% | "
            f"Disk {disk}%"
        )

        return True

    except Exception as e:

        print(
            f"[TASKMANAGER ERROR] {e}"
        )

        speak(
            "I couldn't check the system performance right now."
        )

        return False


# * =========================================================
# * Registry
# * =========================================================

register(
    "taskmanager",
    taskmanager,
)