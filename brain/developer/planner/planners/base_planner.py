"""
JARVIS PRO
Developer Planner

Base Planner
"""

from abc import ABC, abstractmethod

from brain.developer.models.analysis_result import AnalysisResult
from brain.developer.planner.models.execution_plan import ExecutionPlan


class BasePlanner(ABC):
    """
    Base class for all planners.
    """

    @abstractmethod
    def can_handle(self, analysis: AnalysisResult) -> bool:
        """
        Returns True if this planner can handle
        the given analysis.
        """
        pass

    @abstractmethod
    def create_plan(self, analysis: AnalysisResult) -> ExecutionPlan:
        """
        Create an execution plan.
        """
        pass

    def create_base_plan(self, analysis: AnalysisResult) -> ExecutionPlan:
        """
        Create a plan with all common information copied
        from the analysis result.
        """

        plan = ExecutionPlan()

        plan.language = analysis.language
        plan.framework = analysis.framework
        plan.workspace = analysis.workspace
        plan.project_type = analysis.project_type
        plan.runtime = analysis.runtime
        plan.board = analysis.board

        return plan