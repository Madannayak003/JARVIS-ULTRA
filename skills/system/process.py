"""
JARVIS PRO
Process Skill

Provides process listing and process termination.
"""

import psutil

from core.registry import register
from voice.manager import speak


# * =========================================================
# * Running Processes
# * =========================================================

def _list_processes():
    """Return visible running process names."""

    processes = []

    for process in psutil.process_iter(
        ["pid", "name"]
    ):
        try:
            name = process.info.get("name")

            if name:
                processes.append(
                    (
                        process.info["pid"],
                        name,
                    )
                )

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            continue

    return processes


# * =========================================================
# * Process Action
# * =========================================================

def process_action(data=None):
    """
    Handle process-related actions.

    Supported:

        {"action": "running_apps"}

        {"action": "close_process",
         "process": "chrome"}
    """

    if data is None:
        data = {}

    action = str(
        data.get("action", "")
    ).strip().lower()

    # * =====================================================
    # * Running Apps
    # * =====================================================

    if action == "running_apps":

        processes = _list_processes()

        print("\n========== RUNNING PROCESSES ==========\n")

        for pid, name in sorted(
            processes,
            key=lambda item: item[1].lower()
        ):
            print(
                f"{pid:<8} {name}"
            )

        print(
            "\n=======================================\n"
        )

        count = len(processes)

        speak(
            f"There are {count} running processes. "
            "I've listed them in the terminal."
        )

        print(
            f"[PROCESS] Running processes: {count}"
        )

        return True

    # * =====================================================
    # * Close Process
    # * =====================================================

    if action == "close_process":

        target = str(
            data.get("process", "")
        ).strip().lower()

        if not target:

            speak(
                "Which process would you like me to close?"
            )

            return False

        matches = []

        for process in psutil.process_iter(
            ["pid", "name"]
        ):

            try:

                pid = process.info.get("pid")
                name = process.info.get("name")

                if not name:
                    continue

                if target in name.lower():

                    matches.append(
                        (
                            process,
                            pid,
                            name,
                        )
                    )

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
                psutil.ZombieProcess,
            ):
                continue

        # * -------------------------------------------------
        # * Not found
        # * -------------------------------------------------

        if not matches:

            speak(
                f"I couldn't find a running process "
                f"matching {target}."
            )

            print(
                f"[PROCESS] Not found: {target}"
            )

            return True

        # * -------------------------------------------------
        # * Terminate first matching process
        # * -------------------------------------------------

        process, pid, name = matches[0]

        try:

            process.terminate()

            try:

                process.wait(
                    timeout=3
                )

            except psutil.TimeoutExpired:

                process.kill()

            display_name = str(
                data.get("app") or target
            ).strip()

            speak(
                f"I closed {display_name}."
            )

            print(
                f"[PROCESS] Closed: "
                f"{name} (PID {pid})"
            )

            return True

        except psutil.NoSuchProcess:

            speak(
                f"{name} has already closed."
            )

            return True

        except psutil.AccessDenied:

            speak(
                f"I don't have permission to close {name}."
            )

            print(
                f"[PROCESS] Access denied: "
                f"{name} (PID {pid})"
            )

            return False

        except Exception as e:

            print(
                f"[PROCESS ERROR] "
                f"Could not close {name}: {e}"
            )

            speak(
                f"I couldn't close {name}."
            )

            return False

    # * =====================================================
    # * Unknown Action
    # * =====================================================

    print(
        f"[PROCESS] Unknown action: {action}"
    )

    return False


# * =========================================================
# * Registry
# * =========================================================

register(
    "running_apps",
    process_action,
)

register(
    "close_process",
    process_action,
)
