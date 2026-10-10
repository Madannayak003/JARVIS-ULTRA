import os
import datetime

from core.registry import register
from voice.manager import speak
from core.path_resolver import resolve


def info(data=None):

    data = data or {}

    raw_path = data.get("path")

    if not raw_path:

        speak("Which file should I inspect?")

        return False

    path = resolve(
        str(raw_path).strip()
    ) or str(raw_path).strip()

    # * -----------------------------------------------------
    # * Validate
    # * -----------------------------------------------------

    if not os.path.exists(path):

        print(
            f"[FILE INFO] Not found: {path}"
        )

        speak("I couldn't find that file.")

        return False

    # * -----------------------------------------------------
    # * Information
    # * -----------------------------------------------------

    try:

        size = os.path.getsize(path)

        modified = datetime.datetime.fromtimestamp(
            os.path.getmtime(path)
        )

        is_file = os.path.isfile(path)
        is_folder = os.path.isdir(path)

        print()
        print("[FILE INFO]")
        print("Path     :", path)
        print("Name     :", os.path.basename(path))
        print("Size     :", size, "bytes")
        print("Modified :", modified)

        if is_file:
            print("Type     : File")

        elif is_folder:
            print("Type     : Folder")

        print()

        # * -------------------------------------------------
        # * Voice response
        # * -------------------------------------------------

        if is_file:

            speak(
                f"{os.path.basename(path)} is a file."
            )

        elif is_folder:

            speak(
                f"{os.path.basename(path)} is a folder."
            )

        else:

            speak("File information printed.")

        return True

    except Exception as e:

        print(
            f"[FILE INFO ERROR] {e}"
        )

        speak(
            "I couldn't read the file information."
        )

        return False


register(
    "file_info",
    info
)

