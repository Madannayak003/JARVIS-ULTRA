"""
JARVIS PRO
Developer Analyzer

Workspace Detector
"""

from brain.developer.enums import Workspace
from brain.developer.models.analysis_context import AnalysisContext
from brain.developer.analyzer.detectors.base_detector import BaseDetector
from brain.developer.analyzer.rules.workspace_rules import WORKSPACE_RULES


class WorkspaceDetector(BaseDetector):
    """
    Detects the appropriate workspace for a project.
    """

    def detect(self, context: AnalysisContext) -> Workspace:

        words = context.tokens

        for workspace, keywords in WORKSPACE_RULES.items():

            for keyword in keywords:

                if keyword in words:

                    return workspace

        return Workspace.GENERAL