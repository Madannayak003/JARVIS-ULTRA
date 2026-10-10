"""
JARVIS PRO
Developer Editor

Edit Validator
"""

from brain.developer.editor.models.edit_result import (
    EditResult,
)

from brain.developer.editor.validator.syntax_validator import (
    SyntaxValidator,
)


class EditValidator:
    """
    Validates parsed patches before
    they are written to disk.

    Safety checks include:

        - valid file path
        - duplicate patches
        - non-empty content
        - syntax validation
        - suspicious file destruction
    """

    # * --------------------------------------------------
    # * Safety thresholds
    # * --------------------------------------------------

    MIN_PRESERVED_RATIO = 0.35

    MIN_ORIGINAL_LENGTH_FOR_RATIO = 500

    MAX_LINE_REDUCTION = 0.60

    # * --------------------------------------------------

    def __init__(self):

        self.syntax_validator = SyntaxValidator()

    # * --------------------------------------------------

    def validate(
        self,
        result: EditResult,
        original_files: dict[str, str] | None = None,
    ) -> EditResult:
        """
        Validate parsed patches.

        original_files:
            Mapping of relative file path to the
            original complete file content.

        The original files are used to detect
        accidental destructive rewrites.
        """

        seen = set()

        valid = []

        original_files = original_files or {}

        # * --------------------------------------------------
        # * Validate every patch
        # * --------------------------------------------------

        for patch in result.patches:

            # * -----------------------------
            # ! Path required
            # * -----------------------------

            if not patch.path:

                result.errors.append(
                    "Patch has no file path."
                )

                continue

            # * -----------------------------
            # * Duplicate file
            # * -----------------------------

            if patch.path in seen:

                result.errors.append(
                    f"Duplicate patch: {patch.path}"
                )

                continue

            seen.add(
                patch.path
            )

            # * -----------------------------
            # ! Content required
            # * -----------------------------

            if not patch.content.strip():

                result.errors.append(
                    f"{patch.path} is empty."
                )

                continue

            # * -----------------------------
            # * Destructive rewrite check
            # * -----------------------------

            original = original_files.get(
                patch.path
            )

            if original is not None:

                if not self._safe_file_size(
                    patch.path,
                    original,
                    patch.content,
                ):

                    continue

            # * -----------------------------
            # * Syntax Validation
            # * -----------------------------

            success, message = (
                self.syntax_validator.validate(
                    patch,
                )
            )

            if not success:

                result.errors.append(
                    f"{patch.path}: {message}"
                )

                continue

            valid.append(
                patch
            )

        # * --------------------------------------------------
        # * Final result
        # * --------------------------------------------------

        result.patches = valid

        result.success = (
            len(result.errors) == 0
            and len(result.patches) > 0
        )

        return result

    # * --------------------------------------------------
    # * File Size Safety
    # * --------------------------------------------------

    def _safe_file_size(
        self,
        path: str,
        original: str,
        modified: str,
    ) -> bool:
        """
        Detect suspiciously destructive rewrites.

        This is intentionally conservative.

        A small edit is allowed to make a file
        smaller. A massive unexpected reduction
        is rejected.
        """

        original_length = len(
            original
        )

        modified_length = len(
            modified
        )

        # * ------------------------------------------
        # * Small files
        #
        # * Size ratio is unreliable for tiny files.
        # * ------------------------------------------

        if (
            original_length
            < self.MIN_ORIGINAL_LENGTH_FOR_RATIO
        ):

            return True

        # * ------------------------------------------
        # * Character preservation ratio
        # * ------------------------------------------

        ratio = (
            modified_length
            / original_length
        )

        if ratio < self.MIN_PRESERVED_RATIO:

            self._add_destructive_error(
                path,
                (
                    "Modified file is suspiciously "
                    f"small ({modified_length} chars "
                    f"vs {original_length} chars "
                    f"original)."
                ),
            )

            return False

        # * ------------------------------------------
        # * Line reduction
        # * ------------------------------------------

        original_lines = max(
            len(original.splitlines()),
            1,
        )

        modified_lines = len(
            modified.splitlines()
        )

        line_ratio = (
            modified_lines
            / original_lines
        )

        if line_ratio < (
            1 - self.MAX_LINE_REDUCTION
        ):

            self._add_destructive_error(
                path,
                (
                    "Modified file removed too many "
                    f"lines ({modified_lines} vs "
                    f"{original_lines} original)."
                ),
            )

            return False

        return True

    # * --------------------------------------------------
    # ! Error Helper
    # * --------------------------------------------------

    def _add_destructive_error(
        self,
        path: str,
        message: str,
    ) -> None:

        # * This method exists so the validation
        # * logic remains easy to extend later.

        print(
            f"[EDITOR SAFETY] REJECTED: {path}"
        )

        print(
            f"[EDITOR SAFETY] {message}"
        )