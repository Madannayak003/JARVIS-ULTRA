"""
JARVIS PRO
Developer Validator

Structure Validator
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


class StructureValidator(BaseValidator):
    """
    Validates the generated project structure.
    """

    def validate(
        self,
        context: "DeveloperContext",
        result: ValidationResult,
    ) -> None:

        project = context.generated_project

        plan = context.execution_plan

        # * -------------------------------------
        # * Generated folders
        # * -------------------------------------

        generated_folders = set()

        for file in project.files:

            folder = str(PurePosixPath(file.path).parent)

            if folder != ".":

                generated_folders.add(folder)

        # * -------------------------------------
        # * Expected folders
        # * -------------------------------------

        expected_folders = set(plan.folders)

        # * -------------------------------------
        # * Compare
        # * -------------------------------------

        for folder in expected_folders:

            result.total_checks += 1

            if folder in generated_folders:

                result.passed_checks += 1

            else:

                result.failed_checks += 1

                result.error_count += 1

                result.issues.append(

                    ValidationIssue(

                        level=ValidationLevel.ERROR,

                        validator="StructureValidator",

                        file=folder,

                        message="Required folder was not generated.",

                        expected=folder,

                        actual="Missing",

                        suggestion="Generate the missing folder.",

                    )

                )