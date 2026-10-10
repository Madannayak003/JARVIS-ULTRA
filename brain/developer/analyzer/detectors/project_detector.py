"""
JARVIS PRO
Developer Analyzer

Project Detector
"""

from brain.developer.enums import ProjectType
from brain.developer.models.analysis_context import AnalysisContext
from brain.developer.analyzer.detectors.base_detector import BaseDetector
from brain.developer.analyzer.rules.project_rules import PROJECT_RULES


class ProjectDetector(BaseDetector):
    """
    Detects the project type.
    """

    def detect(self, context: AnalysisContext) -> ProjectType:

        words = context.tokens

        for project_type, keywords in PROJECT_RULES.items():

            for keyword in keywords:

                if keyword in words:

                    return project_type

        return ProjectType.UNKNOWN