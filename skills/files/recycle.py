from send2trash import send2trash

from core.registry import register
from voice.manager import speak


def recycle(data):

    path = str(data.get("path", "")).strip()
    if not path:
        speak("Please provide the path to recycle.")
        return False

    send2trash(path)

    speak("Moved to recycle bin.")

    return {
        "ok": True,
        "status": "reported_success",
        "action": "recycle",
        "path": path,
    }


register(
    "recycle",
    recycle
)
