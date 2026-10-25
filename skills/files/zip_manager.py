import shutil

from core.registry import register
from voice.manager import speak

def zip_action(data):

    action = data.get("action")

    if action == "zip":

        folder = data["folder"]

        output = data["output"]

        archive = shutil.make_archive(

            output,

            "zip",

            folder

        )

        speak("Folder compressed successfully.")

        return {
            "ok": True,
            "status": "reported_success",
            "action": "zip",
            "archive": archive,
        }

    elif action == "extract":

        shutil.unpack_archive(

            data["zip"],

            data["destination"]

        )

        speak("Archive extracted.")

        return {
            "ok": True,
            "status": "reported_success",
            "action": "extract",
            "archive": data["zip"],
            "destination": data["destination"],
        }

    return False


register("zip", zip_action)
register("extract", zip_action)
