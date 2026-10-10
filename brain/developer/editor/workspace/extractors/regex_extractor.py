"""
JARVIS PRO
Developer Editor

Regex Extractor
"""

import re

from brain.developer.editor.workspace.extractors.base_extractor import (
    BaseExtractor,
)


class RegexExtractor(BaseExtractor):
    """
    Generic extractor used for Arduino,
    C, C++, HTML, CSS, JS and fallback.
    """

    CONTEXT_LINES = 20

    IGNORE_WORDS = {

        "add",
        "remove",
        "delete",
        "update",
        "replace",
        "rename",
        "fix",
        "repair",
        "modify",
        "change",
        "optimize",
        "format",

    }

    FULL_FILE_ACTIONS = {

        "FORMAT",

    }

    # * --------------------------------------------------

    def extract(
        self,
        request: str,
        edit_type: str,
        content: str,
    ) -> str:

        if not content:

            return ""

        if edit_type in self.FULL_FILE_ACTIONS:

            return content

        words = [

            word.lower()

            for word in re.findall(

                r"[A-Za-z_][A-Za-z0-9_]*",

                request,

            )

            if word.lower() not in self.IGNORE_WORDS

        ]

        lines = content.splitlines()

        for index, line in enumerate(lines):

            lower = line.lower()

            if any(word in lower for word in words):

                start = max(0, index - self.CONTEXT_LINES)
                end = min(len(lines), index + self.CONTEXT_LINES + 1)

                return "\n".join(lines[start:end])

        return "\n".join(lines[:100])