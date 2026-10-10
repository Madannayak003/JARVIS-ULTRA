"""
JARVIS PRO
Developer Generator

Central AI Provider Adapter
"""

from ai.core.service import ai_service

from brain.developer.generator.providers.base_provider import (
    BaseProvider
)

from brain.developer.prompt_builder.models.prompt_result import (
    PromptResult
)


class OllamaProvider(BaseProvider):
    """
    Developer Generator AI adapter.

    Historical class name is preserved so the existing
    Generator architecture does not need to change yet.

    Actual model selection is handled by AIService/AIRouter.
    """

    def __init__(self, system_prompt: str = ""):

        self.system_prompt = system_prompt

    def generate(
        self,
        prompt: PromptResult,
    ) -> str:
        """
        Generate raw text through the central AIService.
        """

        system = (
            prompt.system_prompt
            if prompt.system_prompt
            else self.system_prompt
        )

        print(
            "Developer AI Provider : Sending request..."
        )


        response = ai_service.generate(

            prompt=prompt.user_prompt,

            system_prompt=system,

            capability="coding",

        )

        if not response.success:

            print(
                "Developer AI Provider : Generation failed"
            )

            print(
                "Error:",
                response.error
            )

            return ""

        print(
            "Developer AI Provider : Response received"
        )

        print(
            "Provider:",
            response.provider
        )

        print(
            "Model:",
            response.model
        )

        return response.text