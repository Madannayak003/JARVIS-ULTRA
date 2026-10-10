"""
JARVIS PRO
Developer Planner

Python Planner
"""

from brain.developer.enums import Language

from brain.developer.models.analysis_result import AnalysisResult

from brain.developer.planner.models.execution_plan import ExecutionPlan

from brain.developer.planner.planners.base_planner import BasePlanner

from brain.developer.enums import ProjectType


class PythonPlanner(BasePlanner):
    """
    Planner for Python projects.
    """

    def can_handle(self, analysis: AnalysisResult) -> bool:

        return analysis.language == Language.PYTHON

    def create_plan(self, analysis: AnalysisResult) -> ExecutionPlan:

        plan = self.create_base_plan(analysis)

        # * --------------------------------------------------
        # * Python Script
        # * --------------------------------------------------

        if analysis.project_type == ProjectType.SCRIPT:

            plan.folders = []

            plan.files = [
                "main.py",
            ]

            plan.dependencies = []

            plan.tasks = [
                "Generate Python script",
            ]

            plan.notes.append(
                "Python script plan created."
            )

            return plan

        # * --------------------------------------------------
        # * Full Python Project
        # * --------------------------------------------------

        plan.folders = [
            "src",
            "tests",
            "docs",
        ]

        plan.files = [
            "src/main.py",
            "tests/test_main.py",
            "docs/README.md",
            "requirements.txt",
            ".gitignore",
            "LICENSE",
        ]

        plan.dependencies = []

        plan.tasks = [
            "Create project structure",
            "Generate source files",
            "Install dependencies",
        ]

        plan.notes.append(
            "Python project plan created."
        )

        return plan