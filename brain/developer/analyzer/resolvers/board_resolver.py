from brain.developer.analyzer.resolvers.base_resolver import BaseResolver
from brain.developer.analyzer.rules.board_language_rules import BOARD_LANGUAGE_RULES
from brain.developer.enums.language import Language


class BoardResolver(BaseResolver):

    def resolve(self, analysis):

        if analysis.language != Language.UNKNOWN:
            return

        language = BOARD_LANGUAGE_RULES.get(analysis.board)

        if language:
            analysis.language = language