import os

from pathlib import Path

from core.registry import register
from voice.manager import speak


def recent(data):

    folder = Path.home() / "Downloads"

    try:
        files = sorted(
            (item for item in folder.iterdir() if item.is_file()),
            key=os.path.getmtime,
            reverse=True,
        )[:10]
    except OSError as error:
        print(f"[RECENT FILES ERROR] Unable to inspect {folder}: {error}")
        speak("I couldn't access the Downloads folder.")
        return {"ok": False, "status": "unavailable", "action": "recent_files", "message": "Downloads folder is unavailable."}

    print()

    for f in files:

        print(f)

    print()

    speak("Recent files listed.")

    return {
        "ok": True,
        "status": "no_results" if not files else "reported_success",
        "action": "recent_files",
        "items": [str(item) for item in files],
        "count": len(files),
    }


register(
    "recent_files",
    recent
)
