"""
JARVIS PRO
Developer Planner

ESP32 Planner
"""

from brain.developer.enums import (
    Board,
)

from brain.developer.models.analysis_result import AnalysisResult

from brain.developer.planner.models.execution_plan import ExecutionPlan

from brain.developer.planner.planners.base_planner import BasePlanner


class ESP32Planner(BasePlanner):
    """
    Planner for ESP32 and ESP8266 projects.
    """

    def can_handle(self, analysis: AnalysisResult) -> bool:

        return analysis.board in (

            Board.ESP32,

            Board.ESP8266,

        )

    def create_plan(self, analysis: AnalysisResult) -> ExecutionPlan:

        plan = self.create_base_plan(analysis)

        # * -----------------------------
        # * Default ESP Structure
        # * -----------------------------

        plan.folders = [

            "src",

            "include",

            "lib",

            "data",

            "docs",

        ]

        plan.files = [

            "main.cpp",

            "platformio.ini",

            "README.md",

            ".gitignore",

        ]

        plan.dependencies = []

        plan.tasks = [

            "Create ESP project",

            "Generate firmware",

            "Configure board",

            "Install libraries",

            "Build firmware",

            "Upload firmware",

        ]

        plan.notes.append("ESP32 project plan created.")

        return plan