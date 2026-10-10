"""
JARVIS PRO
Developer Repair

Repair Builder
"""

from brain.developer.repair.models.repair_request import (
    RepairRequest,
)

from brain.developer.validator.models.validation_level import (
    ValidationLevel,
)


class RepairBuilder:
    """
    Builds a repair request from
    the validation report.
    """

    def build(self, context) -> RepairRequest:

        request = RepairRequest()

        validation = context.validation_result

        for issue in validation.issues:

            if issue.level == ValidationLevel.CRITICAL:

                request.errors.append(issue.message)

            elif issue.validator == "FileValidator":

                if issue.expected:

                    request.missing_files.append(
                        issue.expected
                    )

            elif issue.validator == "StructureValidator":

                if issue.expected:

                    request.missing_folders.append(
                        issue.expected
                    )

        return request