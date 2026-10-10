import sys

from voice.manager import speak
from core.context import set_value
from config.settings import get_assistant_display_name


def sleep():

    speak(
        f"Entering sleep mode. Say {get_assistant_display_name()} to wake me."
    )

    set_value(
        "state",
        "sleep"
    )


def wake():

    speak(
        "Welcome back Sir."
    )

    set_value(
        "state",
        "online"
    )


def shutdown():

    speak(
        "Goodbye Sir."
    )

    sys.exit(0)
