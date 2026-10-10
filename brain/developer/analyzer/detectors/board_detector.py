"""
JARVIS PRO
Developer Analyzer

Board Detector
"""

from brain.developer.enums import Board
from brain.developer.models.analysis_context import AnalysisContext
from brain.developer.analyzer.detectors.base_detector import BaseDetector
from brain.developer.analyzer.rules.board_rules import BOARD_RULES


class BoardDetector(BaseDetector):
    """
    Detects development boards from user input.
    """

    def detect(self, context: AnalysisContext) -> Board:

        normalized = context.normalized_text

        for board, keywords in BOARD_RULES.items():

            for keyword in keywords:

                if keyword in normalized:

                    return board

        return Board.NONE