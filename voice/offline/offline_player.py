"""
JARVIS PRO
Offline Audio Player

Completely independent from the online voice system.
Windows-only playback using winsound.
"""

import winsound
from pathlib import Path


def play(file_path):
    """
    Play a WAV file synchronously.
    """

    path = Path(file_path)

    if not path.exists():
        print("[OFFLINE PLAYER] File not found:", path)
        return False

    try:
        winsound.PlaySound(
            str(path),
            winsound.SND_FILENAME
        )

        return True

    except Exception as e:

        print(
            "[OFFLINE PLAYER ERROR]",
            e
        )

        return False


def stop():
    """
    Stop offline playback.
    """

    try:

        winsound.PlaySound(
            None,
            winsound.SND_PURGE
        )

        return True

    except Exception as e:

        print(
            "[OFFLINE PLAYER ERROR]",
            e
        )

        return False