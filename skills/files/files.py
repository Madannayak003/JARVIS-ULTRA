import os
import shutil
import subprocess

from core.registry import register
from voice.manager import speak
from core.confirmation import ask
from send2trash import send2trash
from core.path_resolver import resolve
from skills.files.file_info import info

# * =========================================================
# * Helpers
# * =========================================================

def _resolve_path(value):
    """
    Resolve a JARVIS path if possible.
    Falls back to the original value.
    """

    if not value:
        return None

    value = str(value).strip()

    if not value:
        return None

    resolved = resolve(value)

    if resolved:
        return resolved

    return value


def _path_exists(path):
    """
    Safe existence check.
    """

    try:
        return bool(path) and os.path.exists(path)

    except Exception:
        return False


# * =========================================================
# * File Action
# * =========================================================

def file_action(data=None):

    data = data or {}

    action = data.get("action")

    # * =====================================================
    # * Open File
    # * =====================================================

    if action == "open_file":

        path = _resolve_path(
            data.get("path")
        )

        if not path:

            speak("Which file should I open?")

            return False

        if not _path_exists(path):

            speak("File not found.")

            print(
                f"[FILES] File not found: {path}"
            )

            return False

        if not os.path.isfile(path):

            speak("That path is not a file.")

            return False

        try:

            os.startfile(path)

            print(
                f"[FILES] Opened file: {path}"
            )

            speak("Opening file.")

            return True

        except Exception as e:

            print(
                f"[FILES ERROR] Open file failed: {e}"
            )

            speak("I couldn't open that file.")

            return False

    # * =====================================================
    # * Open Folder
    # * =====================================================

    elif action == "open_folder":

        path = _resolve_path(
            data.get("path")
        )

        if not path:

            speak("Which folder should I open?")

            return False

        try:

            if path == "This PC":

                subprocess.Popen(
                    "explorer shell:MyComputerFolder"
                )

            elif _path_exists(path):

                if not os.path.isdir(path):

                    speak("That path is not a folder.")

                    return False

                subprocess.Popen(
                    f'explorer "{path}"'
                )

            else:

                speak("Folder not found.")

                print(
                    f"[FILES] Folder not found: {path}"
                )

                return False

            print(
                f"[FILES] Opened folder: {path}"
            )

            speak("Opening folder.")

            return True

        except Exception as e:

            print(
                f"[FILES ERROR] Open folder failed: {e}"
            )

            speak("I couldn't open that folder.")

            return False

    # * =====================================================
    # * Create Folder
    # * =====================================================

    elif action == "create_folder":

        path = _resolve_path(
            data.get("path")
        )

        if not path:

            speak("Where should I create the folder?")

            return False

        try:

            os.makedirs(
                path,
                exist_ok=True
            )

            print(
                f"[FILES] Folder created: {path}"
            )

            speak("Folder created.")

            return True

        except Exception as e:

            print(
                f"[FILES ERROR] Create folder failed: {e}"
            )

            speak("I couldn't create that folder.")

            return False

    # * =====================================================
    # * Create File
    # * =====================================================

    elif action == "create_file":

        path = _resolve_path(
            data.get("path")
        )

        if not path:

            speak("What should I name the file?")

            return False

        try:

            parent = os.path.dirname(
                os.path.abspath(path)
            )

            if parent:

                os.makedirs(
                    parent,
                    exist_ok=True
                )

            open(
                path,
                "a",
                encoding="utf-8"
            ).close()

            print(
                f"[FILES] File created: {path}"
            )

            speak("File created.")

            return True

        except Exception as e:

            print(
                f"[FILES ERROR] Create file failed: {e}"
            )

            speak("I couldn't create that file.")

            return False

    # * =====================================================
    # * Copy
    # * =====================================================

    elif action == "copy":

        source = _resolve_path(
            data.get("source")
        )

        destination = _resolve_path(
            data.get("destination")
        )

        if not source or not destination:

            speak("I need both the source and destination.")

            return False

        if not _path_exists(source):

            speak("The source file or folder was not found.")

            return False

        try:

            shutil.copy2(
                source,
                destination
            )

            print(
                f"[FILES] Copied: {source} -> {destination}"
            )

            speak("Copied.")

            return True

        except Exception as e:

            print(
                f"[FILES ERROR] Copy failed: {e}"
            )

            speak("I couldn't copy that.")

            return False

    # * =====================================================
    # * Move
    # * =====================================================

    elif action == "move":

        source = _resolve_path(
            data.get("source")
        )

        destination = _resolve_path(
            data.get("destination")
        )

        if not source or not destination:

            speak("I need both the source and destination.")

            return False

        if not _path_exists(source):

            speak("The source file or folder was not found.")

            return False

        try:

            shutil.move(
                source,
                destination
            )

            print(
                f"[FILES] Moved: {source} -> {destination}"
            )

            speak("Moved.")

            return True

        except Exception as e:

            print(
                f"[FILES ERROR] Move failed: {e}"
            )

            speak("I couldn't move that.")

            return False

    # * =====================================================
    # * Rename
    # * =====================================================

    elif action == "rename":

        old = _resolve_path(
            data.get("old")
        )

        new = _resolve_path(
            data.get("new")
        )

        if not old or not new:

            speak("I need both the old and new names.")

            return False

        if not _path_exists(old):

            speak("The file or folder to rename was not found.")

            return False

        try:

            os.rename(
                old,
                new
            )

            print(
                f"[FILES] Renamed: {old} -> {new}"
            )

            speak("Renamed.")

            return True

        except Exception as e:

            print(
                f"[FILES ERROR] Rename failed: {e}"
            )

            speak("I couldn't rename that.")

            return False

    # * =====================================================
    # * Delete
    # * =====================================================

    elif action == "delete":

        path = _resolve_path(
            data.get("path")
        )

        if not path:

            speak("Which file should I delete?")

            return False

        if not _path_exists(path):

            speak("The file or folder was not found.")

            return False

        # * -------------------------------------------------
        # * Confirmed deletion
        # * -------------------------------------------------

        if data.get("confirmed"):

            try:

                send2trash(path)

                print(
                    f"[FILES] Moved to recycle bin: {path}"
                )

                speak("Deleted.")

                return True

            except Exception as e:

                print(
                    f"[FILES ERROR] Delete failed: {e}"
                )

                speak(
                    "I couldn't delete that file."
                )

                return False

        # * -------------------------------------------------
        # * Ask confirmation
        # * -------------------------------------------------

        ask(
            "delete",
            {
                "action": "delete",
                "path": path,
                "confirmed": True
            }
        )

        speak(
            "Are you sure you want to delete this file?"
        )

        return True

    # * =====================================================
    # * Unknown action
    # * =====================================================

    return False


# * =========================================================
# * Registry
# * =========================================================

register(
    "open_file",
    file_action
)

register(
    "open_folder",
    file_action
)

register(
    "create_file",
    file_action
)

register(
    "create_folder",
    file_action
)

register(
    "copy",
    file_action
)

register(
    "move",
    file_action
)

register(
    "rename",
    file_action
)

register(
    "delete",
    file_action
)