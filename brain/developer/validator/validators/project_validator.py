"""
JARVIS PRO
Developer Validator

Project Validator
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


class ProjectValidator(BaseValidator):
    """
    Performs high-level validation of the generated project.
    """

    def validate(
        self,
        context: "DeveloperContext",
        result: ValidationResult,
    ) -> None:

        project = context.generated_project
        analysis = context.analysis
        plan = context.execution_plan

        # * -------------------------------------
        # * Project Generated
        # * -------------------------------------

        result.total_checks += 1

        if not project.generated:

            result.failed_checks += 1
            result.critical_count += 1

            result.issues.append(

                ValidationIssue(

                    level=ValidationLevel.CRITICAL,

                    validator="ProjectValidator",

                    message="Project generation failed.",

                    suggestion="Regenerate the project.",

                )

            )

            return

        result.passed_checks += 1

        # * -------------------------------------
        # * Files Generated
        # * -------------------------------------

        result.total_checks += 1

        if len(project.files) == 0:

            result.failed_checks += 1
            result.critical_count += 1

            result.issues.append(

                ValidationIssue(

                    level=ValidationLevel.CRITICAL,

                    validator="ProjectValidator",

                    message="Generated project contains no files.",

                    suggestion="Regenerate the project.",

                )

            )

        else:

            result.passed_checks += 1

        # * -------------------------------------
        # * Project Type
        # * -------------------------------------

        result.total_checks += 1

        expected = str(analysis.project_type)
        actual = project.project_type

        if expected == actual:

            result.passed_checks += 1

        else:

            result.failed_checks += 1
            result.error_count += 1

            result.issues.append(

                ValidationIssue(

                    level=ValidationLevel.ERROR,

                    validator="ProjectValidator",

                    message="Generated project type does not match.",

                    expected=expected,

                    actual=actual,

                    suggestion="Regenerate using the correct project type.",

                )

            )

        # * -------------------------------------
        # * Entry File
        # * -------------------------------------

        result.total_checks += 1

        if project.entry_file:

            result.passed_checks += 1

        else:

            result.failed_checks += 1
            result.warning_count += 1

            result.issues.append(

                ValidationIssue(

                    level=ValidationLevel.WARNING,

                    validator="ProjectValidator",

                    message="Entry file is not defined.",

                    suggestion="Set the project's entry file.",

                )

            )

        # * -------------------------------------
        # * Build Command
        # * -------------------------------------

        result.total_checks += 1

        requires_build = (

            project.framework in ("REACT", "NEXTJS")

            or project.workspace in (

                "ESP32",

                "ARDUINO",

            )

        )

        if not requires_build:

            result.passed_checks += 1

        elif project.build_command:

            result.passed_checks += 1

        else:

            result.failed_checks += 1
            result.warning_count += 1

            result.issues.append(

                ValidationIssue(

                    level=ValidationLevel.WARNING,

                    validator="ProjectValidator",

                    message="Build command is missing.",

                )

            )

        # * -------------------------------------
        # * Run Command
        # * -------------------------------------

        result.total_checks += 1

        if project.run_command:

            result.passed_checks += 1

        else:

            result.failed_checks += 1
            result.warning_count += 1

            result.issues.append(

                ValidationIssue(

                    level=ValidationLevel.WARNING,

                    validator="ProjectValidator",

                    message="Run command is missing.",

                )

            )

        # * -------------------------------------
        # * Planned Files
        # * -------------------------------------

        result.total_checks += 1

        planned_files = {

            file.replace("\\", "/")

            for file in (plan.files if plan else [])

        }

        generated_files = {

            file.path.replace("\\", "/").strip()

            for file in project.files

        }

        missing = planned_files - generated_files

        if not missing:

            result.passed_checks += 1

        else:

            result.failed_checks += 1
            result.warning_count += 1

            result.issues.append(

                ValidationIssue(

                    level=ValidationLevel.WARNING,

                    validator="ProjectValidator",

                    message="Some planned files were not generated.",

                    expected=", ".join(sorted(missing)),

                    actual=", ".join(sorted(generated_files)),

                    suggestion="Generate the missing files.",

                )

            )