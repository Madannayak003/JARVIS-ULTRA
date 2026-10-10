import shutil

from core.registry import register
from voice.manager import speak

def zip_action(data):

    action = data.get("action")

    if action == "zip":

        folder = data["folder"]

        output = data["output"]

        shutil.make_archive(

            output,

            "zip",

            folder

        )

        speak("Folder compressed successfully.")

        return True

    elif action == "extract":

        shutil.unpack_archive(

            data["zip"],

            data["destination"]

        )

        speak("Archive extracted.")

        return True

    return False


register("zip", zip_action)
register("extract", zip_action)