"""
JARVIS PRO
Developer Analyzer

Intent Detector
"""

from brain.developer.enums import Intent
from brain.developer.models.analysis_context import AnalysisContext
from brain.developer.analyzer.detectors.base_detector import BaseDetector
from brain.developer.analyzer.rules.intent_rules import INTENT_RULES


class IntentDetector(BaseDetector):
    """
    Detects the developer intent from user input.
    """

    def detect(self, context: AnalysisContext) -> Intent:

        words = context.tokens

        for intent, keywords in INTENT_RULES.items():

            for keyword in keywords:

                if keyword in words:

                    return intent

        return Intent.UNKNOWN