ALIASES = {

    "note": "notepad",
    "notepad": "notepad",

    "calc": "calculator",
    "calculator": "calculator",

    "paint": "paint",

    "cmd": "cmd",
    "terminal": "cmd",
    "command prompt": "cmd",

    "explorer": "file explorer",
    "file explorer": "file explorer",
    "files": "file explorer",

    "settings": "settings",

    "task manager": "task manager",

    "registry": "registry editor",
    "registry editor": "registry editor",

    "device manager": "device manager",
}


def resolve_app(command):

    if not command.startswith("open "):
        return None

    app = command.replace("open", "", 1).strip()

    if app in ALIASES:
        return ALIASES[app]

    return None