"""
JARVIS PRO
AI Core - Model Registry

Central registry for all AI providers and models.

The registry describes models.
It does NOT perform AI generation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# * ==========================================================
# * Model Definition
# * ==========================================================

@dataclass
class ModelDefinition:
    """
    Describes one AI model.
    """

    name: str

    provider: str

    capabilities: List[str] = field(
        default_factory=list
    )

    streaming: bool = True

    vision: bool = False

    local: bool = False

    enabled: bool = True

    priority: int = 100

    description: str = ""


# * ==========================================================
# * Model Registry
# * ==========================================================

class ModelRegistry:
    """
    Central registry of available AI models.
    """

    def __init__(self):

        self._models: Dict[
            str,
            ModelDefinition
        ] = {}

        self._register_defaults()

    # * ======================================================
    # * Register Model
    # * ======================================================

    def register(
        self,
        model: ModelDefinition,
    ) -> None:

        self._models[model.name] = model

    # * ======================================================
    # * Get Model
    # * ======================================================

    def get(
        self,
        model_name: str,
    ) -> Optional[ModelDefinition]:

        return self._models.get(
            model_name
        )

    # * ======================================================
    # * Remove Model
    # * ======================================================

    def remove(
        self,
        model_name: str,
    ) -> None:

        self._models.pop(
            model_name,
            None
        )

    # * ======================================================
    # * All Models
    # * ======================================================

    def all(
        self,
    ) -> List[ModelDefinition]:

        return list(
            self._models.values()
        )

    # * ======================================================
    # * Enabled Models
    # * ======================================================

    def enabled(
        self,
    ) -> List[ModelDefinition]:

        return [
            model
            for model in self._models.values()
            if model.enabled
        ]

    # * ======================================================
    # * Find By Capability
    # * ======================================================

    def find_by_capability(
        self,
        capability: str,
    ) -> List[ModelDefinition]:

        capability = capability.lower()

        return [
            model
            for model in self.enabled()
            if capability in [
                item.lower()
                for item in model.capabilities
            ]
        ]

    # * ======================================================
    # * Default Models
    # * ======================================================

    def _register_defaults(self):

        # * --------------------------------------------------
        # * Ollama - JARVIS
        # * --------------------------------------------------

        self.register(

            ModelDefinition(

                name="jarvis",

                provider="ollama",

                capabilities=[
                    "conversation",
                    "planning",
                    "coding",
                    "reasoning",
                    "editing",
                    "repair",
                    "reasoning",
                    "memory",
                    "offline",
                    "fast",
                ],

                streaming=True,

                local=True,

                priority=50,

                description=(
                    "Local JARVIS Ollama model."
                ),
            )
        )

        # * --------------------------------------------------
        # * Ollama - Qwen 2.5 3B
        # * --------------------------------------------------

        self.register(

            ModelDefinition(

                name="qwen2.5:3b",

                provider="ollama",

                capabilities=[
                    "conversation",
                    "planning",
                    "memory",
                    "editing",
                    "fast",
                    "offline",
                ],

                streaming=True,

                local=True,

                priority=70,

                description=(
                    "Small local Qwen model."
                ),
            )
        )

        # * --------------------------------------------------
        # * Ollama - Qwen 3 4B
        # * --------------------------------------------------

        self.register(

            ModelDefinition(

                name="qwen3:4b",

                provider="ollama",

                capabilities=[
                    "conversation",
                    "planning",
                    "coding",
                    "editing",
                    "reasoning",
                    "memory",
                    "offline",
                ],

                streaming=True,

                local=True,

                priority=60,

                description=(
                    "Local Qwen 3 model."
                ),
            )
        )
        
        # * --------------------------------------------------
        # * Gemini 3.6 Flash - Primary Coding Model
        # * --------------------------------------------------

        self.register(

            ModelDefinition(

                name="gemini-3.6-flash",

                provider="gemini",

                capabilities=[
                    "conversation",
                    "planning",
                    "coding",
                    "developer",
                    "editing",
                    "repair",
                    "reasoning",
                    "memory",
                    "vision",
                    "screen_vision",
                    "fast",
                ],

                streaming=True,

                vision=True,

                local=False,

                enabled=True,

                priority=10,

                description=(
                    "Primary Gemini model for coding, "
                    "reasoning and agentic tasks."
                ),
            )
        )

        # * --------------------------------------------------
        # * Gemini 3.5 Flash - Conversation Fallback
        # * --------------------------------------------------

        self.register(

            ModelDefinition(

                name="gemini-3.5-flash",

                provider="gemini",

                capabilities=[
                    "conversation",
                    "planning",
                    "coding",
                    "developer",
                    "editing",
                    "repair",
                    "reasoning",
                    "memory",
                    "fast",
                    "screen_vision",
                ],

                streaming=True,

                vision=True,

                local=False,

                enabled=True,

                priority=20,

                description=(
                    "Gemini fallback model for "
                    "conversation, reasoning and AI tasks."
                ),
            )
        )

        # * --------------------------------------------------
        # * Gemini 3.5 Flash-Lite - Final Gemini Fallback
        # * --------------------------------------------------

        self.register(

            ModelDefinition(

                name="gemini-3.5-flash-lite",

                provider="gemini",

                capabilities=[
                    "conversation",
                    "planning",
                    "editing",
                    "repair",
                    "file_intelligence",
                    "reasoning",
                    "memory",
                    "fast",
                    "coding",
                    "developer",
                    "screen_vision",
                ],

                streaming=True,

                vision=True,

                local=False,

                enabled=True,

                priority=30,

                description=(
                    "Final Gemini fallback for "
                    "lightweight AI tasks."
                ),
            )
        )

        # * --------------------------------------------------
        # * Gemini 3.1 Flash-Lite - Additional Gemini Fallback
        # * --------------------------------------------------

        self.register(

            ModelDefinition(

                name="gemini-3.1-flash-lite",

                provider="gemini",

                capabilities=[
                    "conversation",
                    "planning",
                    "editing",
                    "repair",
                    "file_intelligence",
                    "reasoning",
                    "memory",
                    "fast",
                    "coding",
                    "developer",
                ],

                streaming=True,

                vision=False,

                local=False,

                enabled=True,

                priority=40,

                description=(
                    "Gemini 3.1 Flash-Lite model for "
                    "lightweight AI tasks."
                ),
            )
        )

        # * --------------------------------------------------
        # * Grok - xAI general AI model
        # * --------------------------------------------------

        self.register(

            ModelDefinition(

                name="grok-4.7",

                provider="grok",

                capabilities=[
                    "conversation",
                    "planning",
                    "coding",
                    "developer",
                    "editing",
                    "repair",
                    "reasoning",
                    "memory",
                    "fast",
                ],

                streaming=True,

                local=False,

                enabled=False,

                priority=15,

                description="Grok model provided by xAI.",
            )
        )
        
        # * --------------------------------------------------
        # * OpenAI GPT - Reasoning / General AI
        # * --------------------------------------------------

        self.register(

            ModelDefinition(

                name="gpt-5.4-mini",

                provider="openai",

                capabilities=[
                    "conversation",
                    "planning",
                    "coding",
                    "editing",
                    "reasoning",
                    "memory",
                    "fast",
                    "screen_vision",
                ],

                streaming=True,

                vision=True,

                local=False,

                enabled=False,

                priority=30,

                description=(
                    "OpenAI GPT model for general "
                    "reasoning, coding and conversation."
                ),
            )
        )
