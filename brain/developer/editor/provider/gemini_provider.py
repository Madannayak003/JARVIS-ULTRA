"""Gemini Lite adapter for Developer Mode editing."""

from typing import Any

from ai.core.service import ai_service
from brain.developer.generator.providers.base_provider import BaseProvider
from core.live_execution import live_developer_generation


class GeminiProvider(BaseProvider):
    """Generate editor changes through the permitted Gemini Lite model."""

    MODEL = "gemini-3.5-flash-lite"

    def __init__(self, system_prompt: str = ""):
        self.system_prompt = system_prompt

    def generate(self, prompt: Any) -> str:
        system = getattr(prompt, "system_prompt", "") or self.system_prompt
        user = getattr(prompt, "user_prompt", "")
        print("Editor AI Provider : Sending request...")
        with live_developer_generation():
            response = ai_service.generate(
                prompt=user,
                system_prompt=system,
                capability="editing",
                provider="gemini",
                model=self.MODEL,
                metadata={"developer_generation": True},
            )
        if not response.success:
            print("[EDITOR AI] Generation failed:", response.error)
            return ""
        print("Editor AI Provider : Response received")
        print("Provider:", response.provider)
        print("Model:", response.model)
        return response.text
