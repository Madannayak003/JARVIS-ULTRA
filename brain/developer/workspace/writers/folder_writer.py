"""
JARVIS PRO
Developer Workspace

Folder Writer
"""

from pathlib import Path


class FolderWriter:
    """
    Creates folders on disk.
    """

    def create(
        self,
        path: str,
    ) -> bool:
        """
        Create a folder.

        Returns True if successful.
        """

        try:

            Path(path).mkdir(

                parents=True,

                exist_ok=True,

            )

            return True

        except Exception:

            return False