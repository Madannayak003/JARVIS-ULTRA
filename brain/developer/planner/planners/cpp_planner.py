"""
JARVIS PRO
Developer Planner

C++ Planner
"""

from brain.developer.enums import Language

from brain.developer.models.analysis_result import AnalysisResult

from brain.developer.planner.models.execution_plan import ExecutionPlan

from brain.developer.planner.planners.base_planner import BasePlanner


class CppPlanner(BasePlanner):
    """
    Planner for C and C++ projects.
    """

    def can_handle(self, analysis: AnalysisResult) -> bool:

        return analysis.language in (
            Language.C,
            Language.CPP,
        )

    def create_plan(self, analysis: AnalysisResult) -> ExecutionPlan:

        plan = self.create_base_plan(analysis)

        # * -----------------------------
        # * Default C/C++ Structure
        # * -----------------------------

        plan.folders = [

            "src",

            "include",

            "build",

            "tests",

        ]

        plan.files = [

            "main.cpp",

            "CMakeLists.txt",

            "README.md",

            ".gitignore",

        ]

        plan.dependencies = []

        plan.tasks = [

            "Create project structure",

            "Generate source files",

            "Configure CMake",

            "Build project",

        ]

        plan.notes.append("C/C++ project plan created.")

        return plan