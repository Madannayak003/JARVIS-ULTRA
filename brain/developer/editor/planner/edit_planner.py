"""
JARVIS PRO
Developer Editor

Edit Planner
"""

from brain.developer.editor.models import (
    EditRequest,
)

from brain.developer.editor.models.edit_plan import (
    EditPlan,
)

from brain.developer.editor.planner.file_selector import (
    FileSelector,
)

from brain.developer.editor.planner.dependency_analyzer import (
    DependencyAnalyzer,
)

from brain.developer.editor.planner.instruction_planner import (
    InstructionPlanner,
)


class EditPlanner:
    """
    Builds an execution plan for the editor.
    """

    def __init__(self):

        self.selector = FileSelector()

        self.dependencies = DependencyAnalyzer()

        self.instructions = InstructionPlanner()

    # * --------------------------------------------------

    def plan(
        self,
        request: EditRequest,
    ) -> EditPlan:

        # * ------------------------------------------
        # * Select primary files
        # * ------------------------------------------

        request.target_files = self.selector.select(

            request,

        )

        # * ------------------------------------------
        # * Expand dependencies
        # * ------------------------------------------

        request = self.dependencies.analyze(

            request,

        )

        # * ------------------------------------------
        # * Build execution plan
        # * ------------------------------------------

        plan = EditPlan()
        
        plan.request = request

        plan.primary_files = list(

            request.primary_files,

        )

        plan.dependent_files = list(

            request.dependent_files,

        )

        plan.target_files = list(

            request.target_files,

        )

        plan.implementation_steps = (

            self.instructions.build(

                request,

            )

        )

        # * ------------------------------------------
        # * Metadata
        # * ------------------------------------------

        plan.estimated_changes = len(

            plan.target_files,

        )

        plan.requires_tests = any(

            "test" in file.lower()

            for file in plan.target_files

        )

        return plan