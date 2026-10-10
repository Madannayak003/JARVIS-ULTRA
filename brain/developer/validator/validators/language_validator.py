"""
JARVIS PRO
Developer Validator

Language Validator
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


class LanguageValidator(BaseValidator):
    """
    Validates the generated project's language.
    """

    def validate(
        self,
        context: "DeveloperContext",
        result: ValidationResult,
    ) -> None:

        project = context.generated_project

        analysis = context.analysis

        result.total_checks += 1

        # * -------------------------------------
        # * No language detected
        # * -------------------------------------

        if not analysis.language:

            result.failed_checks += 1

            result.warning_count += 1

            result.issues.append(

                ValidationIssue(

                    level=ValidationLevel.WARNING,

                    validator="LanguageValidator",

                    message="No language was detected by the analyzer.",

                )

            )

            return

        # * -------------------------------------
        # * Compare
        # * -------------------------------------

        expected = str(analysis.language).strip()

        actual = str(project.language).strip()

        if actual == expected:

            result.passed_checks += 1

        else:

            result.failed_checks += 1

            result.error_count += 1

            result.issues.append(

                ValidationIssue(

                    level=ValidationLevel.ERROR,

                    validator="LanguageValidator",

                    message="Generated project language does not match the requested language.",

                    expected=str(analysis.language),

                    actual=project.language,

                    suggestion="Regenerate the project using the correct programming language.",

                )

            )