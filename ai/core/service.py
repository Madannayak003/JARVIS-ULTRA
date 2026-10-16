"""
JARVIS PRO
AI Core - AI Service

Main public interface for the JARVIS AI Model System.

Consumers such as:
- Chat
- Planner
- Memory
- Developer
- Editor
- Repair

should use AIService instead of calling providers directly.
"""

from typing import Any, Iterator, Optional

from ai.core.router import AIRouter
from ai.core.schemas import (
    AIRequest,
    AIResponse,
    AIStreamChunk,
)

from ai.providers.gemini import GeminiProvider

from ai.providers.openai import OpenAIProvider

from ai.providers.grok import GrokProvider

from ai.core.preference import AIPreference

from ai.core.commands import AICommandHandler


class AIService:
    """
    Main entry point for the JARVIS AI system.
    """

    def __init__(
        self,
        router: Optional[AIRouter] = None,
    ):

        # * --------------------------------------------------
        # * Router
        # * --------------------------------------------------

        self.router = (
            router
            if router is not None
            else AIRouter()
        )

        # * --------------------------------------------------
        # * Register providers
        # * --------------------------------------------------

        self._register_default_providers()

        # * --------------------------------------------------
        # AI Preference
        # * --------------------------------------------------

        self.preference = AIPreference()

    # * ======================================================
    # * Provider Registration
    # * ======================================================

    def _register_default_providers(self):

        # * --------------------------------------------------
        # * Gemini
        # * --------------------------------------------------

        if self.router.get_provider("gemini") is None:

            self.router.register_provider(
                GeminiProvider()
            )

        # * --------------------------------------------------
        # * OpenAI
        # * --------------------------------------------------

        if self.router.get_provider("openai") is None:

            self.router.register_provider(
                OpenAIProvider()
            )

        # * --------------------------------------------------
        # * Grok
        # * --------------------------------------------------

        if self.router.get_provider("grok") is None:

            self.router.register_provider(
                GrokProvider()
            )

    # * ======================================================
    # * Generate
    # * ======================================================

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        capability: str = "conversation",
        provider: Optional[str] = None,
        model: Optional[str] = None,
        output_format: str = "text",
        metadata: Optional[dict] = None,
        images: Optional[list[Any]] = None,
        ) -> AIResponse:
        """
        Generate a complete AI response.
        """

        # Gemini Live is the sole reasoning layer for an active Live turn.
        # Secondary provider calls from legacy AI-dependent skills would
        # violate that contract, so fail explicitly and let the Live model
        # explain the unavailable capability instead of silently falling back.
        from core.live_execution import (
            is_live_developer_generation_allowed,
            is_live_execution,
        )
        live_developer_generation = (
            is_live_execution()
            and capability in {"coding", "editing"}
            and bool((metadata or {}).get("developer_generation"))
            and is_live_developer_generation_allowed()
        )
        if is_live_execution() and not live_developer_generation:
            return AIResponse(
                success=False,
                error="Secondary AI calls are disabled during Gemini Live execution.",
                metadata={"status": "live_only_blocked", "capability": capability},
            )

        # * --------------------------------------------------
        # * Resolve AI Preference
        # * --------------------------------------------------

        selected_provider = (
            provider
            if provider is not None
            else self.preference.provider
        )

        selected_model = (
            model
            if model is not None
            else self.preference.model
        )

        # * --------------------------------------------------
        # * Build Request
        # * --------------------------------------------------

        request = AIRequest(

            prompt=prompt,

            system_prompt=system_prompt,

            capability=capability,

            provider=selected_provider,

            model=selected_model,

            stream=False,

            output_format=output_format,

            metadata=(
                metadata
                if metadata is not None
                else {}
            ),
            
            images=(
                images
                if images is not None
                else []
            ),
        )

        # * --------------------------------------------------
        # * Generate
        # * --------------------------------------------------

        response = self.router.generate(request)
        if response.success and response.provider:
            try:
                from hud.integration import HUDIntegration

                HUDIntegration.ai_model(response.provider, response.model)
            except Exception:
                pass
        return response
        
    # * ======================================================
    # * Stream
    # * ======================================================

    def stream(
        self,
        prompt: str,
        system_prompt: str = "",
        capability: str = "conversation",
        provider: Optional[str] = None,
        model: Optional[str] = None,
        stop_event=None,
        metadata: Optional[dict] = None,
        images: Optional[list[Any]] = None,
        ) -> Iterator[AIStreamChunk]:
        """
        Stream an AI response.
        """

        from core.live_execution import (
            is_live_developer_generation_allowed,
            is_live_execution,
        )
        live_developer_generation = (
            is_live_execution()
            and capability in {"coding", "editing"}
            and bool((metadata or {}).get("developer_generation"))
            and is_live_developer_generation_allowed()
        )
        if is_live_execution() and not live_developer_generation:
            def blocked_stream():
                yield AIStreamChunk(
                    provider="gemini-live",
                    model="",
                    done=True,
                    metadata={
                        "success": False,
                        "status": "live_only_blocked",
                        "error": "Secondary AI calls are disabled during Gemini Live execution.",
                    },
                )
            return blocked_stream()
        
        # * --------------------------------------------------
        # * Resolve AI Preference
        # * --------------------------------------------------

        selected_provider = (
            provider
            if provider is not None
            else self.preference.provider
        )

        selected_model = (
            model
            if model is not None
            else self.preference.model
        )

        request = AIRequest(

            prompt=prompt,

            system_prompt=system_prompt,

            capability=capability,

            provider=selected_provider,
            
            model=selected_model,

            stream=True,

            stop_event=stop_event,

            metadata=(
                metadata
                if metadata is not None
                else {}
            ),
            
            images=(
                images
                if images is not None
                else []
            ),
        )

        provider_stream = self.router.stream(request)

        def report_active_provider():
            reported = False
            for chunk in provider_stream:
                provider_succeeded = (
                    bool(chunk.text)
                    or (
                        chunk.done
                        and chunk.metadata.get("success") is True
                    )
                )
                if not reported and chunk.provider and provider_succeeded:
                    try:
                        from hud.integration import HUDIntegration

                        HUDIntegration.ai_model(chunk.provider, chunk.model)
                    except Exception:
                        pass
                    reported = True
                yield chunk

        return report_active_provider()
        
    # * ======================================================
    # AI Selection Command
    # * ======================================================

    def handle_command(
        self,
        command: str,
    ):
        """
        Handle AI selection commands.

        Examples:
            use Gemini
            use GPT
            use Qwen
            auto mode
        """

        return AICommandHandler.handle(
            command,
            self.preference,
        )    

    def set_provider(self, provider: str) -> str:
        """Set and persist the selected provider mode."""

        self.preference.set_provider(provider)
        return self.preference.mode


# * ==========================================================
# * Shared AI Service
# * ==========================================================

ai_service = AIService()
