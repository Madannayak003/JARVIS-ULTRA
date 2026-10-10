"""
JARVIS PRO
Developer Planner

JavaScript Planner
"""

from brain.developer.enums import Language

from brain.developer.models.analysis_result import AnalysisResult

from brain.developer.planner.models.execution_plan import ExecutionPlan

from brain.developer.planner.planners.base_planner import BasePlanner


class JavaScriptPlanner(BasePlanner):
    """
    Planner for JavaScript and TypeScript projects.
    """

    def can_handle(self, analysis: AnalysisResult) -> bool:

        return analysis.language in (
            Language.JAVASCRIPT,
            Language.TYPESCRIPT,
        )

    def create_plan(self, analysis: AnalysisResult) -> ExecutionPlan:

        plan = self.create_base_plan(analysis)

        # * -----------------------------
        # * Default JavaScript Structure
        # * -----------------------------

        plan.folders = [

            "src",

            "public",

            "tests",

        ]

        plan.files = [

            "package.json",

            "README.md",

            ".gitignore",

        ]

        plan.dependencies = []

        plan.tasks = [

            "Create project structure",

            "Generate source files",

            "Install npm packages",

        ]

        plan.notes.append("JavaScript project plan created.")

        return plan