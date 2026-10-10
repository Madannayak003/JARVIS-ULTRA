"""
JARVIS PRO
Developer Editor

File Selector
"""

from brain.developer.editor.models import (
    EditRequest,
)


class FileSelector:
    """
    Selects which files should be edited.
    """

    KEYWORDS = {

        "readme": [".md"],

        "python": [".py"],
        "main.py": ["main.py"],

        "html": [".html"],

        "css": [".css"],

        "style": [".css"],

        "javascript": [".js"],
        "js": [".js"],

        "typescript": [".ts"],

        "json": [".json"],

        "arduino": [".ino"],

        "esp32": [".ino"],

        "rfid": [".ino"],

    }

    # * --------------------------------------------------

    def select(
        self,
        request: EditRequest,
    ) -> list[str]:

        if not request.target_files:

            return []

        text = request.user_request.lower()

        selected = []

        for keyword, rules in self.KEYWORDS.items():

            if keyword not in text:

                continue

            for file in request.target_files:

                lower = file.lower()

                if any(

                    lower.endswith(rule)

                    or lower == rule

                    or rule in lower

                    for rule in rules

                ):

                    selected.append(file)

        if not selected:

            return request.target_files.copy()

        return sorted(set(selected))