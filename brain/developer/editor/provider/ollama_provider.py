"""
JARVIS PRO
Developer

AI Provider Adapter for Editor
"""

from typing import Any

from ai.core.service import ai_service

from brain.developer.generator.providers.base_provider import (
    BaseProvider
)


class OllamaProvider(BaseProvider):
    """
    Shared AI provider for Developer Editor.

    Historical class name is preserved for compatibility.

    Actual model selection is handled by AIService.
    """

    def __init__(
        self,
        system_prompt: str = "",
    ):

        self.system_prompt = system_prompt

    # * --------------------------------------------------
    # * Generate
    # * --------------------------------------------------

    def generate(
        self,
        prompt: Any,
    ) -> str:

        system = (

            prompt.system_prompt

            if getattr(
                prompt,
                "system_prompt",
                ""
            )

            else self.system_prompt

        )

        user = getattr(

            prompt,

            "user_prompt",

            "",

        )

        print(
            "Editor AI Provider : Sending request..."
        )

        response = ai_service.generate(

            prompt=user,

            system_prompt=system,

            capability="editing",

        )

        if not response.success:

            print(
                "[EDITOR AI] Generation failed:",
                response.error,
            )

            return ""

        print(
            "Editor AI Provider : Response received"
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