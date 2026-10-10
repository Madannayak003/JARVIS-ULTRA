"""
JARVIS PRO
Developer Editor

Code Extractor
"""

from pathlib import Path

from brain.developer.editor.workspace.extractors.python_extractor import (
    PythonExtractor,
)

from brain.developer.editor.workspace.extractors.regex_extractor import (
    RegexExtractor,
)


class CodeExtractor:
    """
    Dispatches extraction to the correct
    language-specific extractor.
    """

    def __init__(self):

        self.python = PythonExtractor()

        self.regex = RegexExtractor()

    # * --------------------------------------------------

    def extract(
        self,
        request: str,
        edit_type: str,
        file_contents: dict[str, str],
    ) -> dict[str, str]:

        result = {}

        for path, content in file_contents.items():

            suffix = Path(path).suffix.lower()

            if suffix == ".py":

                extractor = self.python

            else:

                extractor = self.regex

            result[path] = extractor.extract(

                request,

                edit_type,

                content,

            )

        return result