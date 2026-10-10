"""
JARVIS PRO
Developer Validator

File Validator
"""

from pathlib import PurePosixPath

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


class FileValidator(BaseValidator):
    """
    Validates required project files.
    """

    def validate(
        self,
        context: "DeveloperContext",
        result: ValidationResult,
    ) -> None:

        project = context.generated_project

        plan = context.execution_plan

        # * -------------------------------------
        # * Generated files
        # * -------------------------------------

        generated_files = {

            PurePosixPath(file.path).name

            for file in project.files

        }

        # * -------------------------------------
        # ! Required files
        # * -------------------------------------

        expected_files = {

            PurePosixPath(path).name

            for path in plan.files

        }

        # * -------------------------------------
        # * Compare
        # * -------------------------------------

        for filename in expected_files:

            result.total_checks += 1

            if filename in generated_files:

                result.passed_checks += 1

            else:

                result.failed_checks += 1

                result.error_count += 1

                result.issues.append(

                    ValidationIssue(

                        level=ValidationLevel.ERROR,

                        validator="FileValidator",

                        file=filename,

                        message="Required file was not generated.",

                        expected=filename,

                        actual="Missing",

                        suggestion="Generate the missing file.",

                    )

                )