"""
JARVIS PRO
System Skill

Handles system-level actions:

- Shutdown
- Restart
- Sleep
- Lock

This module preserves the existing registry actions while
providing safer validation and error handling.
"""

import ctypes
import platform
import subprocess

from core.confirmation import ask
from core.registry import register
from voice.manager import speak
from core.listener import request_shutdown
from config.settings import get_assistant_display_name

# * =========================================================
# * Helpers
# * =========================================================

def _is_windows() -> bool:
    """Return True when JARVIS is running on Windows."""
    return platform.system() == "Windows"


def _request_confirmation(action: str, message: str) -> bool:
    """
    Ask the user to confirm a dangerous system action.

    The confirmation data is stored so the confirmation system
    can execute the same action with confirmed=True.
    """

    ask(
        action,
        {
            "action": action,
            "confirmed": True,
        },
    )

    speak(message)

    return True


def _shutdown() -> bool:
    """Shutdown Windows immediately."""
    try:
        subprocess.run(
            ["shutdown", "/s", "/t", "1"],
            check=True,
            capture_output=True,
            text=True,
        )

        return True

    except (OSError, subprocess.SubprocessError) as exc:
        print(f"[SYSTEM] Shutdown failed: {exc}")
        speak("I couldn't shut down the computer.")

        return False


def _restart() -> bool:
    """Restart Windows immediately."""
    try:
        subprocess.run(
            ["shutdown", "/r", "/t", "1"],
            check=True,
            capture_output=True,
            text=True,
        )

        return True

    except (OSError, subprocess.SubprocessError) as exc:
        print(f"[SYSTEM] Restart failed: {exc}")
        speak("I couldn't restart the computer.")

        return False


def _sleep() -> bool:
    """Put Windows into sleep mode."""
    try:
        result = ctypes.windll.powrprof.SetSuspendState(
            False,
            True,
            False,
        )

        if result == 0:
            print("[SYSTEM] Sleep request failed.")
            speak("I couldn't put the computer to sleep.")

            return False

        return True

    except (AttributeError, OSError, ctypes.ArgumentError) as exc:
        print(f"[SYSTEM] Sleep failed: {exc}")
        speak("I couldn't put the computer to sleep.")

        return False


def _lock() -> bool:
    """Lock the Windows workstation."""
    try:
        result = ctypes.windll.user32.LockWorkStation()

        if result == 0:
            print("[SYSTEM] Lock request failed.")
            speak("I couldn't lock the computer.")

            return False

        print("[SYSTEM] Computer locked.")

        return True

    except (AttributeError, OSError, ctypes.ArgumentError) as exc:
        print(f"[SYSTEM] Lock failed: {exc}")
        speak("I couldn't lock the computer.")

        return False
    
    
def _terminate_jarvis() -> bool:
    """Terminate the JARVIS application without shutting down Windows."""

    print(f"[SYSTEM] Terminating {get_assistant_display_name()}.")

    speak("Goodbye Sir.")

    request_shutdown()

    return True


# * =========================================================
# * Main System Action
# * =========================================================

def system_action(data):
    """
    Execute a registered system action.

    Expected data:

        {
            "action": "shutdown",
            "confirmed": True
        }

    Supported actions:

        shutdown
        restart
        sleep
        lock
    """

    if not isinstance(data, dict):
        print(
            "[SYSTEM] Invalid action data:",
            repr(data),
        )

        return False

    action = data.get("action")

    if not isinstance(action, str):
        print(
            "[SYSTEM] Missing or invalid action:",
            repr(action),
        )

        return False

    action = action.strip().lower()
    
    # * =====================================================
    # * JARVIS Application Shutdown
    # * =====================================================

    if action == "terminate_jarvis":

        return _terminate_jarvis()

    # * -----------------------------------------------------
    # * Platform validation
    # * -----------------------------------------------------

    if not _is_windows():
        print(
            f"[SYSTEM] Action '{action}' "
            "is currently supported only on Windows."
        )

        speak(
            "This system action is currently supported "
            "only on Windows."
        )

        return False

    confirmed = bool(
        data.get("confirmed", False)
    )

    # * =====================================================
    # * Shutdown
    # * =====================================================

    if action == "shutdown":

        if not confirmed:

            return _request_confirmation(
                "shutdown",
                "Are you sure you want to shut down your computer?",
            )

        speak("Shutting down the computer.")

        return _shutdown()

    # * =====================================================
    # * Restart
    # * =====================================================

    if action == "restart":

        if not confirmed:

            return _request_confirmation(
                "restart",
                "Are you sure you want to restart your computer?",
            )

        speak("Restarting the computer.")

        return _restart()

    # * =====================================================
    # * Sleep
    # * =====================================================

    if action == "sleep":

        if not confirmed:

            return _request_confirmation(
                "sleep",
                "Do you want me to put the computer to sleep?",
            )

        speak("Putting the computer to sleep.")

        return _sleep()

    # * =====================================================
    # * Lock
    # * =====================================================

    if action == "lock":

        print("[SYSTEM] Locking computer.")

        return _lock()

    # * =====================================================
    # * Unknown system action
    # * =====================================================

    print(
        f"[SYSTEM] Unknown system action: {action}"
    )

    return False


# * =========================================================
# * Registry
# * =========================================================

register(
    "terminate_jarvis",
    system_action,
)

register(
    "shutdown",
    system_action,
)

register(
    "restart",
    system_action,
)

register(
    "sleep",
    system_action,
)

register(
    "lock",
    system_action,
)
