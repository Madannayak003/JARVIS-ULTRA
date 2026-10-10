"""
JARVIS PRO

Central Path Manager

Every module should import paths from here.
"""

from pathlib import Path

# * Project Root
ROOT = Path(__file__).resolve().parent.parent

# * Data Folder
DATA = ROOT / "data"

SCREENSHOTS = DATA / "screenshots"
CAPTURES = DATA / "captures"
RECORDINGS = DATA / "recordings"
GENERATED_IMAGES = DATA / "generated_images"
LOGS = DATA / "logs"
MEMORIES = DATA / "memories"
TEMP = DATA / "temp"
FACES = DATA / "faces"
DOCUMENTS = DATA / "documents"
DOWNLOADS = DATA / "downloads"
CACHE = DATA / "cache"
EXPORTS = DATA / "exports"

# * Automatically create folders
for folder in [

    DATA,

    SCREENSHOTS,

    CAPTURES,

    RECORDINGS,

    GENERATED_IMAGES,

    LOGS,

    MEMORIES,

    TEMP,

    FACES,

    DOCUMENTS,

    DOWNLOADS,

    CACHE,

    EXPORTS

]:
    folder.mkdir(
        parents=True,
        exist_ok=True
    )
