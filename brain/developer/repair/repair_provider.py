"""
JARVIS PRO
Developer Repair

Repair Provider
"""

from ai.core.service import ai_service

from brain.developer.prompt_builder.models.prompt_result import (
    PromptResult,
)


class RepairProvider:
    """
    Sends repair prompts to the AI.
    """

    def generate(
        self,
        prompt: PromptResult,
    ) -> str:
        """
        Send repair prompts through the central AIService.
        """

        response = ai_service.generate(

            prompt=prompt.user_prompt,

            system_prompt=prompt.system_prompt,

            capability="coding",

        )

        if not response.success:

            print(
                "[REPAIR AI] Generation failed:",
                response.error,
            )

            return ""

        print(
            "[REPAIR AI] Provider:",
            response.provider,
        )

        print(
            "[REPAIR AI] Model:",
            response.model,
        )

        return response.text