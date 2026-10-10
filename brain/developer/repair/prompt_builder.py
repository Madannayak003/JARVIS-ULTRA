"""
JARVIS PRO
Developer Repair

Repair Prompt Builder
"""

from brain.developer.repair.models.repair_prompt import (
    RepairPrompt,
)

from brain.developer.repair.builders.repair_context_builder import (
    RepairContextBuilder,
)

from brain.developer.repair.builders.repair_instruction_builder import (
    RepairInstructionBuilder,
)


class RepairPromptBuilder:
    """
    Builds the prompt used by
    the Repair Engine.
    """

    def __init__(self):

        self.context_builder = RepairContextBuilder()

        self.instruction_builder = RepairInstructionBuilder()

    # * -----------------------------------------------------

    def build(self, request) -> RepairPrompt:

        prompt = RepairPrompt()

        prompt.system_prompt = (
            "You are __ASSISTANT_NAME__ Repair Engine.\n"
            "Generate ONLY the missing files.\n"
            "Do NOT regenerate existing files."
        )

        prompt.user_prompt = "\n\n".join(

            [

                self.context_builder.build(request),

                self.instruction_builder.build(request),

            ]

        )

        return prompt
