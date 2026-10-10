"""
JARVIS PRO
Developer Editor

Python Extractor
"""

import ast

from brain.developer.editor.workspace.extractors.base_extractor import (
    BaseExtractor,
)


class PythonExtractor(BaseExtractor):
    """
    AST-based extractor for Python files.

    Strategy
    --------
    Small files:
        Return the entire file.

    Large files:
        Extract only the relevant function/class.
    """

    # * Maximum number of lines to send entirely
    FULL_FILE_LIMIT = 300

    # * --------------------------------------------------

    def extract(
        self,
        request: str,
        edit_type: str,
        content: str,
    ) -> str:

        if not content:

            return ""

        # * ------------------------------------------
        # * Small project?
        # * Send the whole file.
        # * ------------------------------------------

        lines = content.splitlines()

        if len(lines) <= self.FULL_FILE_LIMIT:

            return content

        # * ------------------------------------------
        # * Large project
        # * AST extraction
        # * ------------------------------------------

        try:

            tree = ast.parse(content)

        except Exception:

            return content

        request = request.lower()

        for node in ast.walk(tree):

            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):

                if node.name.lower() not in request:

                    continue

                start = node.lineno - 1

                end = getattr(

                    node,

                    "end_lineno",

                    start + 1,

                )

                return "\n".join(

                    lines[start:end]

                )

            if isinstance(node, ast.ClassDef):

                if node.name.lower() not in request:

                    continue

                start = node.lineno - 1

                end = getattr(

                    node,

                    "end_lineno",

                    start + 1,

                )

                return "\n".join(

                    lines[start:end]

                )

        # * ------------------------------------------
        # * Fallback
        # * ------------------------------------------

        return content