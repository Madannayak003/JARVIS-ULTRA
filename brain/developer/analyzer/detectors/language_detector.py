"""
JARVIS PRO
Developer Analyzer

Language Detector
"""

from brain.developer.enums import Language
from brain.developer.models.analysis_context import AnalysisContext
from brain.developer.analyzer.detectors.base_detector import BaseDetector
from brain.developer.analyzer.rules.language_rules import LANGUAGE_RULES


class LanguageDetector(BaseDetector):
    """
    Detects the programming language from user input.
    """

    def detect(self, context: AnalysisContext) -> Language:

        words = context.tokens

        for language, keywords in LANGUAGE_RULES.items():

            for keyword in keywords:

                if keyword in words:

                    return language

        return Language.UNKNOWN