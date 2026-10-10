"""
JARVIS PRO
Developer Editor

File Reader
"""

from pathlib import Path


class FileReader:
    """
    Reads the contents of selected files.
    """

    MAX_FILE_SIZE = 1024 * 1024  # * 1 MB

    # * --------------------------------------------------

    def read(
        self,
        project_path: str,
        files: list[str],
    ) -> dict[str, str]:
        """
        Read selected project files.

        Returns:

        {
            "src/main.py": "...",
            "README.md": "...",
        }
        """

        result: dict[str, str] = {}

        root = Path(project_path)

        if not root.exists():

            return result

        for relative_path in files:

            file_path = root / relative_path

            if not file_path.exists():

                result[relative_path] = ""

                continue

            if not file_path.is_file():

                result[relative_path] = ""

                continue

            try:

                if file_path.stat().st_size > self.MAX_FILE_SIZE:

                    result[relative_path] = ""

                    continue

                result[relative_path] = file_path.read_text(

                    encoding="utf-8",

                    errors="replace",

                )

            except Exception:

                result[relative_path] = ""

        return result