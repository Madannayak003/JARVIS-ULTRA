"""
JARVIS PRO
Developer Editor

Response Parser
"""

from brain.developer.editor.models.edit_result import (
    EditResult,
)

from brain.developer.editor.parser.file_parser import (
    FileParser,
)


class ResponseParser:
    """
    Converts an LLM response into
    structured editor results.
    """

    def __init__(self):

        self.file_parser = FileParser()

    # * --------------------------------------------------

    def parse(
        self,
        response: str,
    ) -> EditResult:

        result = EditResult()

        result.patches = self.file_parser.parse(

            response,

        )

        result.success = len(

            result.patches

        ) > 0

        if result.success:

            result.message = (

                f"Parsed {len(result.patches)} file(s)."

            )

        else:

            result.message = (

                "No editable files found."

            )

        return result