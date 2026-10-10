"""
JARVIS PRO
Developer Editor

Syntax Validator
"""

import ast

from brain.developer.editor.models.patch import (
    Patch,
)


class SyntaxValidator:
    """
    Validates generated code before it is written.

    Current:
        Python syntax validation.

    Future:
        HTML validation
        JSON validation
        C/C++ parsing
        JavaScript parsing
    """

    # * --------------------------------------------------

    def validate(
        self,
        patch: Patch,
    ) -> tuple[bool, str]:

        extension = patch.path.rsplit(".", 1)[-1].lower()

        # * ------------------------------------------
        # * Python
        # * ------------------------------------------

        if extension == "py":

            try:

                ast.parse(

                    patch.content,

                )

            except SyntaxError as error:

                return (

                    False,

                    f"Python syntax error: {error}",

                )

        # * ------------------------------------------

        return (

            True,

            "",

        )