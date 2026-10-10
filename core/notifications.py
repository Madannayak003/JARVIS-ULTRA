"""Shared native desktop notification helper based on the verified Mark flow."""

from __future__ import annotations

import platform
import subprocess
import time


def notify_windows_toast(title: str, body: str) -> bool:
    """Show a Windows notification using Mark's verified fallback chain."""

    if platform.system() != "Windows":
        return False

    message = str(body)
    notified = False
    mechanism = ""

    try:
        from plyer import notification

        notification.notify(title=str(title), message=message, timeout=15)
        notified = True
        mechanism = "plyer"
    except Exception:
        pass

    if not notified:
        try:
            from win10toast import ToastNotifier

            ToastNotifier().show_toast(
                str(title),
                message,
                duration=15,
                threaded=False,
            )
            notified = True
            mechanism = "win10toast"
        except Exception:
            pass

    # * Mark's last-resort Windows fallback.
    if not notified:
        try:
            subprocess.run(["msg", "*", "/TIME:30", message], check=False)
        except Exception as error:
            pass

    try:
        import winsound

        for frequency in (800, 1000, 1200):
            winsound.Beep(frequency, 180)
            time.sleep(0.08)
    except Exception:
        pass

    if notified:
        print(f"[NOTIFICATIONS] Windows toast delivered via {mechanism}.")
    return notified
