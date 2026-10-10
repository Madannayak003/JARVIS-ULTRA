from send2trash import send2trash

from core.registry import register
from voice.manager import speak


def recycle(data):

    send2trash(data["path"])

    speak("Moved to recycle bin.")

    return True


register(
    "recycle",
    recycle
)