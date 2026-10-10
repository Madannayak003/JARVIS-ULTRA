"""
JARVIS PRO
AI Core - Model Manager

Responsible for selecting models using:
- Model Registry
- AI Model Policy
- Provider preferences
- Explicit model/provider overrides

The ModelManager does NOT call AI providers.
"""

from typing import List, Optional

from ai.core.policy import AIModelPolicy
from ai.core.registry import (
    ModelDefinition,
    ModelRegistry,
)


class ModelManager:
    """
    Selects the most appropriate model for a capability.
    """

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        policy=AIModelPolicy,
    ):

        self.registry = (
            registry
            if registry is not None
            else ModelRegistry()
        )

        self.policy = policy
        
    # * ======================================================
    # * Capability Model Preferences
    # * ======================================================

    CAPABILITY_MODEL_PREFERENCES = {

        "conversation": [
            "gemini-3.5-flash-lite",
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
        ],

        "fast": [
            "gemini-3.5-flash-lite",
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
        ],

        "coding": [
            "gemini-3.5-flash-lite",
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.1-flash-lite",
        ],

        "developer": [
            "gemini-3.5-flash-lite",
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.1-flash-lite",
        ],

        "editing": [
            "gemini-3.5-flash-lite",
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.1-flash-lite",
        ],

        "repair": [
            "gemini-3.5-flash-lite",
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.1-flash-lite",
        ],

        "reasoning": [
            "gemini-3.5-flash-lite",
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
        ],

        "planning": [
            "gemini-3.5-flash-lite",
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
        ],

        "screen_vision": [
            "gemini-3.5-flash-lite",
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
        ],
    }

    # * ======================================================
    # * Get Explicit Model
    # * ======================================================

    def get_model(
        self,
        model_name: str,
    ) -> Optional[ModelDefinition]:

        return self.registry.get(
            model_name
        )

    # * ======================================================
    # * Find Models By Capability
    # * ======================================================

    def find_models(
        self,
        capability: str,
    ) -> List[ModelDefinition]:

        models = self.registry.find_by_capability(
            capability
        )

        return sorted(
            models,
            key=lambda model: model.priority
        )

    # * ======================================================
    # * Policy Provider Order
    # * ======================================================

    def _policy_order(
        self,
        capability: str,
    ) -> List[str]:

        return self.policy.providers_for(
            capability
        )

    # * ======================================================
    # * Policy-aware Model Selection
    # * ======================================================

    def select(
        self,
        capability: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Optional[ModelDefinition]:

        # * --------------------------------------------------
        # * Explicit model override
        # * --------------------------------------------------

        if model:

            selected = self.registry.get(
                model
            )

            if selected is None:
                return None

            if not selected.enabled:
                return None

            return selected

        # * --------------------------------------------------
        # * Explicit provider override
        # * --------------------------------------------------

        if provider:

            provider = provider.lower()

            candidates = [
                item
                for item in self.find_models(
                    capability
                )
                if item.provider.lower()
                == provider
            ]

            if not candidates:

                return None

            return candidates[0]

        # * --------------------------------------------------
        # * Normal policy-based selection
        # * --------------------------------------------------

        candidates = self.find_models(
            capability
        )

        if not candidates:

            return None

        provider_order = self._policy_order(
            capability
        )

        # * --------------------------------------------------
        # * Follow policy preference
        # * --------------------------------------------------

        for preferred_provider in provider_order:

            preferred_provider = (
                preferred_provider.lower()
            )

            for candidate in candidates:

                if (
                    candidate.provider.lower()
                    == preferred_provider
                ):

                    return candidate

        # * --------------------------------------------------
        # * Fallback to priority
        # * --------------------------------------------------

        return candidates[0]

    # * ======================================================
    # * Get All Policy Candidates
    # * ======================================================

        # * ======================================================
    # * Get All Policy Candidates
    # * ======================================================

    def candidates(
        self,
        capability: str,
        provider: Optional[str] = None,
    ) -> List[ModelDefinition]:

        capability = (
            capability
            .strip()
            .lower()
        )

        models = self.find_models(
            capability
        )

        # * --------------------------------------------------
        # * Explicit provider
        # * --------------------------------------------------

        if provider:

            provider = provider.lower()

            models = [
                model
                for model in models
                if model.provider.lower()
                == provider
            ]

            return models

        # * --------------------------------------------------
        # * Provider policy
        # * --------------------------------------------------

        provider_order = self._policy_order(
            capability
        )

        # * --------------------------------------------------
        # * Model preference for this capability
        # * --------------------------------------------------

        preferred_models = (
            self.CAPABILITY_MODEL_PREFERENCES.get(
                capability,
                []
            )
        )

        ordered = []

        # * --------------------------------------------------
        # * Follow provider policy first
        # * --------------------------------------------------

        for preferred_provider in provider_order:

            preferred_provider = (
                preferred_provider.lower()
            )

            provider_models = [

                model

                for model in models

                if model.provider.lower()
                == preferred_provider
            ]

            # * ----------------------------------------------
            # * Apply capability-specific model preference
            # * ----------------------------------------------

            if preferred_models:

                for preferred_model in preferred_models:

                    for model in provider_models:

                        if (
                            model.name.lower()
                            == preferred_model.lower()
                        ):

                            if model not in ordered:
                                ordered.append(model)

            # * ----------------------------------------------
            # * Add remaining models for this provider
            # * in their normal priority order.
            # * ----------------------------------------------

            for model in provider_models:

                if model not in ordered:

                    ordered.append(model)

        # * --------------------------------------------------
        # * Add unlisted providers
        # * --------------------------------------------------

        for model in models:

            if model not in ordered:

                ordered.append(model)

        return ordered

    # * ======================================================
    # * Default Model
    # * ======================================================

    def default(
        self,
    ) -> Optional[ModelDefinition]:

        models = self.registry.enabled()

        if not models:

            return None

        return sorted(
            models,
            key=lambda model: model.priority
        )[0]
