"""
JARVIS PRO
Developer Editor

Python Applier
"""

from brain.developer.editor.workspace.appliers.base_applier import (
    BaseApplier,
)


class PythonApplier(BaseApplier):
    """
    Python-specific patch applier.

    Current Version
    ----------------
    - Accepts complete files.
    - Falls back to original file if generated code is empty.

    Future Versions
    ----------------
    - AST Function Merge
    - AST Class Merge
    - Rename Support
    - Multi-function Patching
    - Import Preservation
    """

    # * --------------------------------------------------

    def apply(
        self,
        original: str,
        generated: str,
    ) -> str:

        generated = generated.strip()

        # * Nothing generated
        if not generated:

            return original

        # * --------------------------------------------------
        # * Phase 8
        #
        # * Full-file replacement.
        #
        # * Phase 9+
        #
        # * Replace this section with AST merge.
        # * --------------------------------------------------

        return generated + "\n"