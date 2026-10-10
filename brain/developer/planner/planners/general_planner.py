"""
JARVIS PRO
Developer Planner

General Planner
"""

from brain.developer.models.analysis_result import AnalysisResult
from brain.developer.planner.models.execution_plan import ExecutionPlan
from brain.developer.planner.planners.base_planner import BasePlanner


class GeneralPlanner(BasePlanner):
    """
    Fallback planner for unsupported or generic projects.
    """

    def can_handle(self, analysis: AnalysisResult) -> bool:
        """
        General planner can handle any request.
        """
        return True

    def create_plan(self, analysis: AnalysisResult) -> ExecutionPlan:
        """
        Create a basic execution plan.
        """

        plan = self.create_base_plan(analysis)

        plan.folders = []

        plan.files = []

        plan.dependencies = []

        plan.tasks = []

        plan.notes.append("General execution plan created.")

        return plan