"""
JARVIS PRO
Developer Editor

Text Applier
"""

from brain.developer.editor.workspace.appliers.base_applier import (
    BaseApplier,
)


class TextApplier(BaseApplier):
    """
    Default patch applier.

    This is used for plain text and any language that
    does not yet have a specialized patch engine.

    Current behavior:
        Replace the entire file.

    Future:
        Line-based merge.
    """

    # * --------------------------------------------------

    def apply(
        self,
        original: str,
        generated: str,
    ) -> str:

        generated = generated.strip()

        if not generated:

            return original

        return generated + "\n"