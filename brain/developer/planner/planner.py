"""
JARVIS PRO
Developer Planner

Planner Engine
"""

from brain.developer.models.analysis_result import AnalysisResult
from brain.developer.planner.models.execution_plan import ExecutionPlan

from brain.developer.planner.rules.planner_rules import (
    BOARD_PLANNER_RULES,
    FRAMEWORK_PLANNER_RULES,
    LANGUAGE_PLANNER_RULES,
    WORKSPACE_PLANNER_RULES,
)

from brain.developer.planner.planners.general_planner import GeneralPlanner


class Planner:
    """
    Main Planner Engine.

    Selects the most specific planner and
    generates an execution plan.
    """

    def __init__(self):

        self._planner_cache = {}

    def _get_planner(self, planner_class):

        if planner_class not in self._planner_cache:
            self._planner_cache[planner_class] = planner_class()

        return self._planner_cache[planner_class]

    def _select_planner(self, analysis: AnalysisResult):
        """
        Planner selection priority

        1. Board
        2. Workspace
        3. Framework
        4. Language
        5. General
        """

        # * -------------------------
        # * Board
        # * -------------------------

        planner_class = BOARD_PLANNER_RULES.get(
            analysis.board
        )

        if planner_class:
            return planner_class

        # * -------------------------
        # * Workspace
        # * -------------------------

        planner_class = WORKSPACE_PLANNER_RULES.get(
            analysis.workspace
        )

        if planner_class:
            return planner_class

        # * -------------------------
        # * Framework
        # * -------------------------

        planner_class = FRAMEWORK_PLANNER_RULES.get(
            analysis.framework
        )

        if planner_class:
            return planner_class

        # * -------------------------
        # * Language
        # * -------------------------

        planner_class = LANGUAGE_PLANNER_RULES.get(
            analysis.language
        )

        if planner_class:
            return planner_class

        # * -------------------------
        # * Fallback
        # * -------------------------

        return GeneralPlanner

    def create_plan(self, analysis: AnalysisResult) -> ExecutionPlan:
        """
        Generate an execution plan from an analysis result.
        """

        planner_class = self._select_planner(analysis)

        planner = self._get_planner(planner_class)

        if planner.can_handle(analysis):
            return planner.create_plan(analysis)

        return self._get_planner(GeneralPlanner).create_plan(analysis)