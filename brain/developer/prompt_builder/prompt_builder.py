"""
JARVIS PRO
Developer Prompt Builder

Prompt Builder Engine
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from brain.developer.context import DeveloperContext

from brain.developer.prompt_builder.models.prompt_context import PromptContext
from brain.developer.prompt_builder.models.prompt_result import PromptResult

from brain.developer.prompt_builder.builders.system_builder import SystemBuilder
from brain.developer.prompt_builder.builders.context_builder import ContextBuilder
from brain.developer.prompt_builder.builders.instruction_builder import (
    InstructionBuilder,
)


class PromptBuilder:
    """
    Builds the final LLM prompt.
    """

    def __init__(self):

        self.system_builder = SystemBuilder()

        self.context_builder = ContextBuilder()

        self.instruction_builder = InstructionBuilder()

    # * --------------------------------------------------

    def build(
        self,
        context: "DeveloperContext",
    ) -> PromptResult:
        """     
        Build the final prompt from the DeveloperContext.
        """

        # * --------------------------------------------
        # * Prompt Context
        # * --------------------------------------------

        prompt_context = PromptContext(

            user_request=context.user_request,

            analysis=context.analysis,

            execution_plan=context.execution_plan,

        )

        # * --------------------------------------------
        # * Build Prompt Parts
        # * --------------------------------------------

        system_prompt = self.system_builder.build(
            prompt_context
        )

        project_context = self.context_builder.build(
            prompt_context
        )

        instructions = self.instruction_builder.build(
            prompt_context
        )

        # * --------------------------------------------
        # * Final Prompt
        # * --------------------------------------------

        user_prompt = (
            project_context
            + "\n\n"
            + instructions
        )

        prompt = (
            system_prompt
            + "\n\n"
            + user_prompt
        )

        return PromptResult(

            system_prompt=system_prompt,

            user_prompt=user_prompt,

            prompt=prompt,

        )