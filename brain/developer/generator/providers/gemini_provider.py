"""Gemini Lite adapter for Developer Mode project generation."""

from ai.core.service import ai_service
from core.live_execution import live_developer_generation

from brain.developer.generator.providers.base_provider import BaseProvider
from brain.developer.prompt_builder.models.prompt_result import PromptResult


class GeminiProvider(BaseProvider):
    """Generate Developer Mode output through the permitted Gemini Lite model."""

    MODEL = "gemini-3.5-flash-lite"

    def __init__(self, system_prompt: str = ""):
        self.system_prompt = system_prompt

    def generate(self, prompt: PromptResult) -> str:
        system = prompt.system_prompt or self.system_prompt
        print("Developer AI Provider : Sending request...")
        with live_developer_generation():
            response = ai_service.generate(
                prompt=prompt.user_prompt,
                system_prompt=system,
                capability="coding",
                provider="gemini",
                model=self.MODEL,
                metadata={"developer_generation": True},
            )
        if not response.success:
            print("Developer AI Provider : Generation failed")
            print("Error:", response.error)
            return ""
        print("Developer AI Provider : Response received")
        print("Provider:", response.provider)
        print("Model:", response.model)
        return response.text
