"""
JARVIS PRO
Developer Workspace

File Writer
"""

from pathlib import Path


class FileWriter:
    """
    Writes files to disk.
    """

    def write(
        self,
        path: str,
        content: str,
        encoding: str = "utf-8",
    ) -> bool:
        """
        Write a file.

        Returns True if successful.
        """

        try:

            file = Path(path)

            # * -------------------------------------
            # * Ensure parent folders exist
            # * -------------------------------------

            file.parent.mkdir(

                parents=True,

                exist_ok=True,

            )

            # * -------------------------------------
            # * Write File
            # * -------------------------------------

            file.write_text(

                content,

                encoding=encoding,

            )

            return True

        except Exception:

            return False