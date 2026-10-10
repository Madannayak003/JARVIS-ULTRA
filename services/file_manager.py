from pathlib import Path

from core.paths import (
    CAPTURES,
    RECORDINGS,
    SCREENSHOTS,
)


# * --------------------------------------------------
# * Internal Helper
# * --------------------------------------------------

def _latest_file(folder, extensions):

    folder = Path(folder)

    if not folder.exists():
        return None

    files = []

    for ext in extensions:

        files.extend(folder.glob(ext))

    if not files:
        return None

    return max(
        files,
        key=lambda f: f.stat().st_mtime
    )


# * --------------------------------------------------
# * Photos
# * --------------------------------------------------

def latest_photo():

    return _latest_file(
        CAPTURES,
        [
            "*.jpg",
            "*.jpeg",
            "*.png",
            "*.bmp",
            "*.webp"
        ]
    )


# * --------------------------------------------------
# * Screenshots
# * --------------------------------------------------

def latest_screenshot():

    return _latest_file(
        SCREENSHOTS,
        [
            "*.png",
            "*.jpg",
            "*.jpeg"
        ]
    )


# * --------------------------------------------------
# * Videos
# * --------------------------------------------------

def latest_video():

    return _latest_file(
        RECORDINGS,
        [
            "*.mp4",
            "*.avi",
            "*.mov",
            "*.mkv"
        ]
    )


# * --------------------------------------------------
# * Find File by Name
# * --------------------------------------------------

from pathlib import Path
import os

HOME = Path.home()

SEARCH_FOLDERS = [

    HOME / "Desktop",
    HOME / "Documents",
    HOME / "Downloads",
    HOME / "Pictures",
    HOME / "Videos",
    HOME / "Music",

    Path(CAPTURES),
    Path(SCREENSHOTS),
    Path(RECORDINGS)
]

def find_file(filename):

    filename = filename.lower().strip()

    matches = []

    for folder in SEARCH_FOLDERS:

        folder = Path(folder)

        if not folder.exists():
            continue

        try:

            for file in folder.rglob("*"):

                if not file.is_file():
                    continue

                name = file.stem.lower()
                full = file.name.lower()

                if (
                    filename == name
                    or filename == full
                    or filename in name
                    or filename in full
                ):

                    matches.append(file)

        except Exception:

            continue

    if not matches:
        return []

    matches.sort(
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )

    return matches


# * --------------------------------------------------
# * Generic Latest File
# * --------------------------------------------------

def latest_file(folder):

    folder = Path(folder)

    if not folder.exists():
        return None

    files = [

        f

        for f in folder.iterdir()

        if f.is_file()

    ]

    if not files:
        return None

    return max(
        files,
        key=lambda f: f.stat().st_mtime
    )
    
def search_files(query="", extension=None, limit=20):
    """
    Search common user folders for files.

    query:
        Text to match against filename.

    extension:
        Optional extension such as ".pdf" or "pdf".

    limit:
        Maximum number of results.
    """

    query = str(query or "").strip().lower()

    if extension:
        extension = str(extension).strip().lower()

        if not extension.startswith("."):
            extension = "." + extension

    matches = []

    for folder in SEARCH_FOLDERS:

        folder = Path(folder)

        if not folder.exists():
            continue

        try:

            for file in folder.rglob("*"):

                if not file.is_file():
                    continue

                name = file.name.lower()

                if query and query not in name:
                    continue

                if extension and file.suffix.lower() != extension:
                    continue

                matches.append(file)

        except Exception:
            continue

    matches.sort(
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )

    return matches[:limit]