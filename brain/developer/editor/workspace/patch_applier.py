"""
JARVIS PRO
Developer Editor

Patch Applier
"""

from pathlib import Path

from brain.developer.editor.models.patch import (
    Patch,
)

from brain.developer.editor.workspace.appliers.python_applier import (
    PythonApplier,
)

from brain.developer.editor.workspace.appliers.text_applier import (
    TextApplier,
)


class PatchApplier:
    """
    Applies parsed patches to existing files.

    Dispatches each patch to the correct language-specific
    applier based on the file extension.
    """

    def __init__(self):

        # * ------------------------------------------
        # * Language-specific appliers
        # * ------------------------------------------

        self.appliers = {

            ".py": PythonApplier(),

        }

        # * ------------------------------------------
        # * Default fallback
        # * ------------------------------------------

        self.default_applier = TextApplier()

    # * --------------------------------------------------

    def apply(
        self,
        project_path: str,
        patch: Patch,
    ) -> str:

        root = Path(project_path)

        target = root / patch.path

        # * ------------------------------------------
        # * Read existing file
        # * ------------------------------------------

        original = ""

        if target.exists():

            original = target.read_text(

                encoding="utf-8",

            )

        # * ------------------------------------------
        # * Detect file type
        # * ------------------------------------------

        extension = target.suffix.lower()

        # * ------------------------------------------
        # * Select appropriate applier
        # * ------------------------------------------

        applier = self.appliers.get(

            extension,

            self.default_applier,

        )

        # * ------------------------------------------
        # * Apply patch
        # * ------------------------------------------

        return applier.apply(

            original,

            patch.content,

        )