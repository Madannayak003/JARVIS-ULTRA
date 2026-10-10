"""
JARVIS PRO
Developer Validator

Validator Engine
"""

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from brain.developer.context import DeveloperContext

from brain.developer.validator.models.validation_result import (
    ValidationResult,
)

from brain.developer.validator.validators.structure_validator import (
    StructureValidator,
)

from brain.developer.validator.validators.file_validator import (
    FileValidator,
)

from brain.developer.validator.validators.language_validator import (
    LanguageValidator,
)

from brain.developer.validator.validators.framework_validator import (
    FrameworkValidator,
)

from brain.developer.validator.validators.dependency_validator import (
    DependencyValidator,
)

from brain.developer.validator.validators.project_validator import (
    ProjectValidator,
)

from brain.developer.validator.validators.content_validator import (
    ContentValidator,
)


class Validator:
    """
    Main Validator Engine.

    Executes all validators and produces
    a ValidationResult.
    """

    def __init__(self):

        self.validators = [

            StructureValidator(),

            FileValidator(),

            LanguageValidator(),

            FrameworkValidator(),

            DependencyValidator(),

            ProjectValidator(),

            ContentValidator(),

        ]

    # * -----------------------------------------------------

    def validate(
        self,
        context: "DeveloperContext",
    ) -> ValidationResult:
        """
        Validate the generated project.
        """

        start_time = time.perf_counter()

        result = ValidationResult()

        # * -------------------------------------
        # * Execute Validators
        # * -------------------------------------

        for validator in self.validators:

            validator.validate(

                context,

                result,

            )

        # * -------------------------------------
        # * Statistics
        # * -------------------------------------

        project = context.generated_project

        result.validated_files = len(project.files)

        folders = {

            file.path.replace("\\", "/").rsplit("/", 1)[0]

            for file in project.files

            if "/" in file.path.replace("\\", "/")

        }

        result.validated_folders = len(folders)

        # * -------------------------------------
        # * Validation Score
        # * -------------------------------------

        score = 100

        score -= result.warning_count * 2

        score -= result.error_count * 10

        score -= result.critical_count * 25

        score = max(0, min(score, 100))

        result.score = score

        # * -------------------------------------
        # * Validation Grade
        # * -------------------------------------

        if score >= 97:

            result.grade = "A+"

        elif score >= 90:

            result.grade = "A"

        elif score >= 80:

            result.grade = "B"

        elif score >= 70:

            result.grade = "C"

        elif score >= 60:

            result.grade = "D"

        else:

            result.grade = "F"

        # * -------------------------------------
        # * Overall Status
        # * -------------------------------------

        result.valid = (

            result.error_count == 0

            and

            result.critical_count == 0

        )

        # * -------------------------------------
        # * Execution Time
        # * -------------------------------------

        result.execution_time_ms = round(

            (time.perf_counter() - start_time) * 1000,

            2,

        )

        # * -------------------------------------
        # * Summary
        # * -------------------------------------

        status = "PASSED" if result.valid else "FAILED"

        result.summary = (

            f"{status} | "

            f"{result.passed_checks}/{result.total_checks} checks passed | "

            f"{result.warning_count} warnings | "

            f"{result.error_count} errors | "

            f"{result.critical_count} critical | "

            f"Score {result.score} ({result.grade})"

        )

        # * -------------------------------------
        # * Generator Confidence
        # * -------------------------------------

        project.confidence = float(result.score)

        # * -------------------------------------
        # * Metadata
        # * -------------------------------------

        result.metadata["validator_count"] = len(self.validators)

        result.metadata["validated_files"] = result.validated_files

        result.metadata["validated_folders"] = result.validated_folders

        result.metadata["execution_time_ms"] = result.execution_time_ms

        return result