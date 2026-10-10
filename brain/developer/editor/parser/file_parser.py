"""
JARVIS PRO
Developer Editor

File Parser
"""

import re

from brain.developer.editor.models.patch import (
    Patch,
)


class FileParser:
    """
    Parses '# FILE:' sections from an LLM response.
    """

    FILE_PATTERN = re.compile(

        r"# FILE:\s*(.+?)\n```(\w+)?\n(.*?)```",

        re.DOTALL,

    )

    # * --------------------------------------------------

    def parse(
        self,
        response: str,
    ) -> list[Patch]:

        patches = []

        for match in self.FILE_PATTERN.finditer(

            response,

        ):

            path = match.group(1).strip()

            language = (

                match.group(2) or ""

            ).strip()

            content = match.group(3).rstrip()

            patches.append(

                Patch(

                    path=path,

                    language=language,

                    content=content,

                )

            )

        return patches