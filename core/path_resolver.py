"""
Smart Windows Path Resolver
"""

"""
JARVIS PRO
Smart Path Resolver v2
"""

import os
from pathlib import Path

HOME = Path.home()

ONEDRIVE = HOME / "OneDrive"

if ONEDRIVE.exists():

    DESKTOP = ONEDRIVE / "Desktop"
    DOCUMENTS = ONEDRIVE / "Documents"
    PICTURES = ONEDRIVE / "Pictures"

else:

    DESKTOP = HOME / "Desktop"
    DOCUMENTS = HOME / "Documents"
    PICTURES = HOME / "Pictures"

DOWNLOADS = HOME / "Downloads"
VIDEOS = HOME / "Videos"
MUSIC = HOME / "Music"

PATHS = {

    "desktop": str(DESKTOP),

    "documents": str(DOCUMENTS),

    "downloads": str(DOWNLOADS),

    "pictures": str(PICTURES),

    "videos": str(VIDEOS),

    "music": str(MUSIC),

    "home": str(HOME),

    "this pc": "This PC",

    "my computer": "This PC",

    "computer": "This PC",

    "my projects": r"D:\MY FILES\MY-VSCODE\VS-CODE",

    "jarvis project": r"D:\MY FILES\MY-VSCODE\VS-CODE\JARVIS-main\JARVIS-PRO"
}


def resolve(location):

    if not location:
        return None

    location = location.lower().strip()

    # * Remove common words
    for word in [
        "open",
        "my",
        "folder",
        "directory"
    ]:

        location = location.replace(word, "").strip()

    # * Known folders
    if location in PATHS:
        return PATHS[location]

    # * Drive letters
    for drive in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":

        if location in [
            f"{drive.lower()} drive",
            f"{drive.lower()}:",
            drive.lower()
        ]:

            return f"{drive}:\\"

    return None