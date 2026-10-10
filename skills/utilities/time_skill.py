from datetime import datetime

from core.registry import register
from voice.manager import speak


def current_time(data):

    now = datetime.now().strftime("%I:%M %p")

    speak(f"The time is {now}")

    return True


register("time", current_time)