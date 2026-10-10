"""
Background Services
"""

from services.remote_control import RemoteControlServer
from core.diagnostics import debug_print

SERVICES = {


}

_phone_call_monitor = None
_scheduler_started = False


def start_all():

    debug_print("[SERVICES] Ready")

    global _scheduler_started
    try:
        from skills.memory.reminders import start_scheduler as start_reminder_scheduler
        start_reminder_scheduler()
        debug_print("[SERVICES] Reminder scheduler started.")
    except Exception as error:
        print(f"[SERVICES] Reminder scheduler unavailable: {error}")
    try:
        from skills.automation.scheduling import start_scheduler
        _scheduler_started = start_scheduler()
        debug_print("[SERVICES] Scheduler started.")
    except Exception as error:
        print(f"[SERVICES] Scheduler unavailable: {error}")

    global _phone_call_monitor
    try:
        from skills.phone_call.monitor import start_phone_call_monitor

        _phone_call_monitor = start_phone_call_monitor()
        debug_print("[SERVICES] Phone Call monitor started.")
    except Exception as error:
        print(f"[SERVICES] Phone Call monitor unavailable: {error}")


def stop_all():
    global _phone_call_monitor, _scheduler_started
    try:
        from skills.memory.reminders import stop_scheduler as stop_reminder_scheduler
        stop_reminder_scheduler()
    except Exception as error:
        print(f"[SERVICES] Reminder scheduler shutdown skipped: {error}")
    try:
        from skills.automation.scheduling import stop_scheduler
        stop_scheduler()
        _scheduler_started = False
    except Exception as error:
        print(f"[SERVICES] Scheduler shutdown skipped: {error}")
    if _phone_call_monitor is None:
        return
    try:
        from skills.phone_call.monitor import stop_phone_call_monitor

        stop_phone_call_monitor()
        debug_print("[SERVICES] Phone Call monitor stopped.")
    except Exception as error:
        print(f"[SERVICES] Phone Call monitor shutdown skipped: {error}")
    finally:
        _phone_call_monitor = None
    
remote_server = None

def start_remote_control(command_handler):
    global remote_server

    remote_server = RemoteControlServer(
        command_handler=command_handler
    )

    if remote_server.start():
        print(
            "[REMOTE] Open:",
            remote_server.url()
        )

    return remote_server
