"""
JARVIS PRO
Developer Analyzer

Language Resolver
"""

from brain.developer.enums import (
    Language,
    Workspace,
)

from brain.developer.models.analysis_result import AnalysisResult

from brain.developer.analyzer.rules.framework_language_rules import (
    FRAMEWORK_LANGUAGE_RULES,
)

from brain.developer.analyzer.resolvers.base_resolver import BaseResolver


class LanguageResolver(BaseResolver):
    """
    Infers the programming language.
    """

    def resolve(self, analysis: AnalysisResult) -> None:

        # * ------------------------------------
        # * Already detected
        # * ------------------------------------

        if analysis.language != Language.UNKNOWN:
            return

        # * ------------------------------------
        # * Workspace Rules
        # * ------------------------------------

        if analysis.workspace == Workspace.ARDUINO:
            analysis.language = Language.CPP
            return

        if analysis.workspace == Workspace.ESP32:
            analysis.language = Language.CPP
            return

        # * ------------------------------------
        # * Framework Rules
        # * ------------------------------------

        language = FRAMEWORK_LANGUAGE_RULES.get(
            analysis.framework
        )

        if language is not None:

            analysis.language = language