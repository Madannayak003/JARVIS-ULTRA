"""
JARVIS PRO
Developer Analyzer

Runtime Detector
"""

from brain.developer.enums import Runtime
from brain.developer.models.analysis_context import AnalysisContext
from brain.developer.analyzer.detectors.base_detector import BaseDetector
from brain.developer.analyzer.rules.runtime_rules import RUNTIME_RULES


class RuntimeDetector(BaseDetector):
    """
    Detects where the project runs.
    """

    def detect(self, context: AnalysisContext) -> Runtime:

        words = context.tokens

        for runtime, keywords in RUNTIME_RULES.items():

            for keyword in keywords:

                if keyword in words:

                    return runtime

        return Runtime.UNKNOWN