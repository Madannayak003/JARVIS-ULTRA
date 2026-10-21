"""
JARVIS ULTRA
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

# The registry intentionally contains only supported Gemini models.
# No alternate provider registrations remain in this registry.
