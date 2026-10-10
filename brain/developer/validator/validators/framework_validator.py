"""
JARVIS PRO
Developer Validator

Framework Validator
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

from brain.developer.enums import Framework


class FrameworkValidator(BaseValidator):
    """
    Validates the generated project's framework.
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
        # * No framework requested
        # * -------------------------------------

        if analysis.framework == Framework.NONE:

            result.passed_checks += 1

            return

        # * -------------------------------------
        # * Compare
        # * -------------------------------------

        expected = str(analysis.framework).strip()

        actual = str(project.framework or "").strip()

        if actual == expected:

            result.passed_checks += 1

        else:

            result.failed_checks += 1

            result.error_count += 1

            result.issues.append(

                ValidationIssue(

                    level=ValidationLevel.ERROR,

                    validator="FrameworkValidator",

                    message="Generated project framework does not match the requested framework.",

                    expected=expected,

                    actual=actual,

                    suggestion="Regenerate the project using the correct framework.",

                )

            )