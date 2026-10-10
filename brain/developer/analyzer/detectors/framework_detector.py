"""
JARVIS PRO
Developer Analyzer

Framework Detector
"""

from brain.developer.enums import Framework
from brain.developer.models.analysis_context import AnalysisContext
from brain.developer.analyzer.detectors.base_detector import BaseDetector
from brain.developer.analyzer.rules.framework_rules import FRAMEWORK_RULES


class FrameworkDetector(BaseDetector):
    """
    Detects frameworks from user input.
    """

    def detect(self, context: AnalysisContext) -> Framework:

        words = context.tokens

        for framework, keywords in FRAMEWORK_RULES.items():

            for keyword in keywords:

                if keyword in words:

                    return framework

        return Framework.NONE