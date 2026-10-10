"""
JARVIS PRO
Developer Editor

Instruction Planner
"""

from brain.developer.editor.models import (
    EditRequest,
)


class InstructionPlanner:
    """
    Generates implementation steps for the editor.
    """

    def build(
        self,
        request: EditRequest,
    ) -> list[str]:

        steps = []

        action = request.edit_type.upper()

        if action == "ADD":

            steps.extend(

                [

                    "Implement the requested feature.",

                    "Integrate it with the existing code.",

                    "Preserve existing behaviour.",

                ]

            )

        elif action == "FIX":

            steps.extend(

                [

                    "Fix the reported issue.",

                    "Preserve existing behaviour where possible.",

                    "Avoid introducing regressions.",

                ]

            )

        elif action == "UPDATE":

            steps.extend(

                [

                    "Update the existing implementation.",

                    "Keep backward compatibility when possible.",

                ]

            )

        elif action == "RENAME":

            steps.extend(

                [

                    "Rename every occurrence consistently.",

                    "Update imports and references.",

                    "Update unit tests if required.",

                ]

            )

        elif action == "REPLACE":

            steps.extend(

                [

                    "Replace the requested implementation.",

                    "Update dependent code.",

                    "Update tests if required.",

                ]

            )

        elif action == "OPTIMIZE":

            steps.extend(

                [

                    "Improve performance.",

                    "Do not change behaviour.",

                ]

            )

        elif action == "FORMAT":

            steps.extend(

                [

                    "Format the selected files.",

                    "Do not change program behaviour.",

                ]

            )

        else:

            steps.append(

                "Apply the requested edit."

            )

        return steps