"""
JARVIS PRO
Developer Prompt Builder

System Builder
"""

from brain.developer.prompt_builder.builders.base_builder import BaseBuilder

from brain.developer.prompt_builder.models.prompt_context import PromptContext

from brain.developer.prompt_builder.rules.system_rules import SYSTEM_RULES


class SystemBuilder(BaseBuilder):
    """
    Builds the system prompt.
    """

    def build(self, context: PromptContext) -> str:

        return "\n".join(SYSTEM_RULES)