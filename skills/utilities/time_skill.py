from datetime import datetime

from core.registry import register
from voice.manager import speak


def current_time(data):

    now = datetime.now().strftime("%I:%M %p")

    speak(f"The time is {now}")

    return {
        "ok": True,
        "status": "reported_success",
        "action": "time",
        "time": now,
    }


register("time", current_time)
