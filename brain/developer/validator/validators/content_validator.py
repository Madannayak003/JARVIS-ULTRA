"""
JARVIS PRO
Developer Validator

Content Validator
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from brain.developer.context import DeveloperContext

from brain.developer.validator.models.validation_issue import (
    ValidationIssue,
)

from brain.developer.validator.models.validation_level import (
    ValidationLevel,
)

from brain.developer.validator.models.validation_result import (
    ValidationResult,
)

from brain.developer.validator.validators.base_validator import (
    BaseValidator,
)


class ContentValidator(BaseValidator):
    """
    Validates the contents of generated files.
    """

    PLACEHOLDERS = (

        "TODO",
        "FIXME",
        "pass",
        "NotImplemented",
        "NotImplementedError",
        "...",

    )

    # * ---------------------------------------------------------

    def validate(
        self,
        context: "DeveloperContext",
        result: ValidationResult,
    ) -> None:

        project = context.generated_project

        for file in project.files:

            result.total_checks += 1

            content = file.content.strip()

            # * -------------------------------------
            # * Empty File
            # * -------------------------------------

            if not content:

                result.failed_checks += 1

                result.warning_count += 1

                result.issues.append(

                    ValidationIssue(

                        level=ValidationLevel.WARNING,

                        validator="ContentValidator",

                        file=file.path,

                        message="Generated file is empty.",

                        suggestion="Generate complete file contents.",

                    )

                )

                continue

            # * -------------------------------------
            # * Placeholder Detection
            # * -------------------------------------

            found_placeholder = False

            for token in self.PLACEHOLDERS:

                if token in content:

                    found_placeholder = True

                    result.failed_checks += 1

                    result.warning_count += 1

                    result.issues.append(

                        ValidationIssue(

                            level=ValidationLevel.WARNING,

                            validator="ContentValidator",

                            file=file.path,

                            message=f"Placeholder detected: {token}",

                            suggestion="Replace placeholder with real implementation.",

                        )

                    )

            if found_placeholder:

                continue

            # * -------------------------------------
            # * Very Small Source File
            # * -------------------------------------

            if (

                file.extension

                in (

                    ".py",

                    ".cpp",

                    ".c",

                    ".h",

                    ".hpp",

                    ".ino",

                    ".js",

                    ".ts",

                )

                and

                len(content.splitlines()) < 3

            ):

                result.failed_checks += 1

                result.warning_count += 1

                result.issues.append(

                    ValidationIssue(

                        level=ValidationLevel.WARNING,

                        validator="ContentValidator",

                        file=file.path,

                        message="Source file appears unusually small.",

                        suggestion="Verify the generated implementation.",

                    )

                )

                continue

            # * -------------------------------------
            # * Passed
            # * -------------------------------------

            result.passed_checks += 1