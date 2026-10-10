import os

from pathlib import Path

from core.registry import register
from voice.manager import speak


def recent(data):

    folder = Path.home() / "Downloads"

    files = sorted(

        folder.iterdir(),

        key=os.path.getmtime,

        reverse=True

    )[:10]

    print()

    for f in files:

        print(f)

    print()

    speak("Recent files listed.")

    return True


register(
    "recent_files",
    recent
)