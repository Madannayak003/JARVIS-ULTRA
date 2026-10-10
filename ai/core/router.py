"""
JARVIS PRO
AI Core - AI Router

Central runtime AI routing system.

Responsibilities:
- Select providers using ModelManager policy
- Check provider availability
- Try preferred models in order
- Fallback when a provider is unavailable
- Fallback when generation fails
- Support streaming
- Detect temporary model quota failures
- Temporarily skip models that return 429 RESOURCE_EXHAUSTED
"""

import re
import threading
import time

from typing import Dict, Optional

from ai.core.model_manager import ModelManager

from ai.core.schemas import (
    AIRequest,
    AIResponse,
    AIStreamChunk,
)

from ai.providers.base import AIProvider
from core.diagnostics import debug_print


class AIRouter:
    """
    Central AI runtime router.

    Includes temporary model cooldown protection.

    Example:

        Gemini 3.6
            ↓
        429 RESOURCE_EXHAUSTED
            ↓
        model cooldown
            ↓
        Gemini 3.5 Flash Lite
    """

    # * ======================================================
    # * Configuration
    # * ======================================================

    # * How long a model remains temporarily skipped after
    # * a quota/rate-limit failure.
    #
    # * 15 minutes is intentionally long enough to prevent
    # * repeated useless requests while still allowing the
    # * model to recover during the same JARVIS session.
    MODEL_COOLDOWN_SECONDS = 15 * 60

    def __init__(
        self,
        model_manager: Optional[ModelManager] = None,
    ):

        self.model_manager = (
            model_manager
            if model_manager is not None
            else ModelManager()
        )

        self.providers: Dict[
            str,
            AIProvider
        ] = {}

        # * --------------------------------------------------
        # * Temporary model cooldowns
        #
        # * {
        # * "gemini:gemini-3.6-flash": expiry_timestamp
        # * }
        # * --------------------------------------------------

        self._model_cooldowns = {}

        self._cooldown_lock = threading.Lock()

    # * ======================================================
    # * Provider Registration
    # * ======================================================

    def register_provider(
        self,
        provider: AIProvider,
    ) -> None:

        self.providers[
            provider.name.lower()
        ] = provider

    # * ======================================================
    # * Provider Lookup
    # * ======================================================

    def get_provider(
        self,
        provider_name: str,
    ) -> Optional[AIProvider]:

        if not provider_name:
            return None

        return self.providers.get(
            provider_name.lower()
        )

    # * ======================================================
    # * Model Cooldown Key
    # * ======================================================

    def _cooldown_key(
        self,
        provider_name: str,
        model_name: str,
    ) -> str:

        return (
            f"{provider_name.lower()}:"
            f"{model_name.lower()}"
        )

    # * ======================================================
    # ! Detect Quota / Rate Limit Error
    # * ======================================================

    def _is_quota_error(
        self,
        error,
        provider_name: str = "",
    ) -> bool:
        """
        Detect temporary quota/rate-limit failures.

        Handles errors such as:

        429
        RESOURCE_EXHAUSTED
        quota exceeded
        rate limit
        too many requests
        """

        if error is None:
            return False

        text = str(error).lower()

        patterns = (
            "429",
            "resource_exhausted",
            "quota exceeded",
            "quotaexceeded",
            "rate limit",
            "rate_limit",
            "too many requests",
        )

        if any(
            pattern in text
            for pattern in patterns
        ):
            return True

        # Gemini can temporarily reject an otherwise valid model with a
        # 503/UNAVAILABLE response during service pressure or high demand.
        # Keep this scoped to Gemini so unrelated provider/configuration
        # errors containing "unavailable" are not cooled down accidentally.
        if provider_name.lower() == "gemini":
            return (
                "503" in text
                or "high demand" in text
                or "service unavailable" in text
                or text.strip() == "unavailable"
                or (
                    bool(re.search(r"\bunavailable\b", text))
                    and any(
                        marker in text
                        for marker in ("model", "gemini", "service")
                    )
                )
            )

        return False

    # * ======================================================
    # * Put Model On Cooldown
    # * ======================================================

    def _cooldown_model(
        self,
        provider_name: str,
        model_name: str,
        error=None,
    ) -> None:
        """
        Temporarily disable a model after a quota/rate-limit
        failure.

        This does NOT disable the provider permanently.

        It only affects this AIRouter instance.
        """

        key = self._cooldown_key(
            provider_name,
            model_name,
        )

        cooldown_seconds = (
            self.MODEL_COOLDOWN_SECONDS
        )

        # * --------------------------------------------------
        # * Try to extract a server-provided retry delay.
        #
        # * Example:
        #
        # * retryDelay: '17s'
        #
        # ! We do NOT blindly trust very small retry values
        # ! for daily quota errors.
        #
        # * Minimum cooldown remains configurable.
        # * --------------------------------------------------

        if error:

            text = str(error)

            match = re.search(
                r"retryDelay['\"]?\s*:\s*['\"]?"
                r"(\d+)"
                r"\s*s",
                text,
                re.IGNORECASE,
            )

            if match:

                try:

                    retry_seconds = int(
                        match.group(1)
                    )

                    # * Only extend the cooldown if the
                    # * provider asks for a longer delay.
                    cooldown_seconds = max(
                        cooldown_seconds,
                        retry_seconds,
                    )

                except Exception:
                    pass

        expires_at = (
            time.monotonic()
            + cooldown_seconds
        )

        with self._cooldown_lock:

            self._model_cooldowns[
                key
            ] = expires_at

        debug_print(
            "[AI ROUTER] Model cooldown:",
            provider_name,
            model_name,
            f"({cooldown_seconds}s)",
        )

    # * ======================================================
    # * Check Model Cooldown
    # * ======================================================

    def _is_model_on_cooldown(
        self,
        provider_name: str,
        model_name: str,
    ) -> bool:

        key = self._cooldown_key(
            provider_name,
            model_name,
        )

        now = time.monotonic()

        with self._cooldown_lock:

            expires_at = (
                self._model_cooldowns.get(key)
            )

            if expires_at is None:

                return False

            # * --------------------------------------------------
            # * Cooldown expired
            # * --------------------------------------------------

            if now >= expires_at:

                self._model_cooldowns.pop(
                    key,
                    None,
                )

                debug_print(
                    "[AI ROUTER] Model cooldown expired:",
                    provider_name,
                    model_name,
                )

                return False

            return True

    # * ======================================================
    # * Remaining Cooldown
    # * ======================================================

    def _cooldown_remaining(
        self,
        provider_name: str,
        model_name: str,
    ) -> int:

        key = self._cooldown_key(
            provider_name,
            model_name,
        )

        now = time.monotonic()

        with self._cooldown_lock:

            expires_at = (
                self._model_cooldowns.get(key)
            )

            if expires_at is None:
                return 0

            remaining = (
                expires_at - now
            )

            if remaining <= 0:

                self._model_cooldowns.pop(
                    key,
                    None,
                )

                return 0

            return int(
                remaining
            )

    # * ======================================================
    # * Candidate Models
    # * ======================================================

    def _get_candidates(
        self,
        request: AIRequest,
    ):

        # * --------------------------------------------------
        # * Explicit model
        # * --------------------------------------------------

        if request.model:

            model = self.model_manager.get_model(
                request.model
            )

            if model is None:
                return []

            if not model.enabled:
                return []

            return [model]

        # * --------------------------------------------------
        # * Policy-aware candidates
        # * --------------------------------------------------

        candidates = self.model_manager.candidates(
            request.capability
        )

        # * --------------------------------------------------
        # * Explicit provider filter
        # * --------------------------------------------------

        if request.provider:

            provider_name = (
                request.provider.lower()
            )

            candidates = [

                model

                for model in candidates

                if model.provider.lower()
                == provider_name

            ]

        else:
            # * AUTO remains provider-first, but Gemini needs to retain its
            # * capability-specific model chain so an unavailable preferred
            # * model can fall through to the next configured Gemini model.
            # * Keep one configured model for every other provider so their
            # * existing fallback order remains exactly:
            # * Gemini -> Grok -> OpenAI -> Ollama.
            seen_providers = set()
            ordered_candidates = []
            for model in candidates:
                provider_name = model.provider.lower()
                if provider_name == "gemini":
                    ordered_candidates.append(model)
                    continue
                if provider_name in seen_providers:
                    continue
                seen_providers.add(provider_name)
                ordered_candidates.append(model)
            candidates = ordered_candidates

        return candidates

    # * ======================================================
    # * Route Only
    # * ======================================================

    def route(
        self,
        request: AIRequest,
    ):

        candidates = self._get_candidates(
            request
        )

        if not candidates:

            raise RuntimeError(
                "No AI models available for "
                f"capability: {request.capability}"
            )

        # * --------------------------------------------------
        # * Find first available provider/model
        # * --------------------------------------------------

        for model in candidates:

            # * ----------------------------------------------
            # * Temporary cooldown
            # * ----------------------------------------------

            if self._is_model_on_cooldown(
                model.provider,
                model.name,
            ):

                remaining = (
                    self._cooldown_remaining(
                        model.provider,
                        model.name,
                    )
                )

                debug_print(
                    "[AI ROUTER] Model on cooldown:",
                    model.provider,
                    model.name,
                    f"({remaining}s remaining)",
                )

                continue

            provider = self.get_provider(
                model.provider
            )

            if provider is None:

                debug_print(
                    "[AI ROUTER] Provider not registered:",
                    model.provider,
                )

                continue

            if not provider.is_available():

                debug_print(
                    "[AI ROUTER] Provider unavailable:",
                    model.provider,
                    model.name,
                )

                continue

            request.model = model.name

            request.provider = model.provider

            debug_print(
                "[AI ROUTER] Selected:",
                model.provider,
                model.name,
            )

            return provider

        raise RuntimeError(
            "No available AI provider/model for "
            f"capability: {request.capability}"
        )

    # * ======================================================
    # * Generate With Fallback
    # * ======================================================

    def generate(
        self,
        request: AIRequest,
    ) -> AIResponse:

        candidates = self._get_candidates(
            request
        )

        if not candidates:

            return AIResponse(

                text="",

                provider="",

                model="",

                success=False,

                error=(
                    "No AI models available for "
                    f"capability: {request.capability}"
                ),
            )

        last_error = None

        # * --------------------------------------------------
        # * Try every candidate in policy order
        # * --------------------------------------------------

        for model in candidates:

            # * ----------------------------------------------
            # * Temporary cooldown
            # * ----------------------------------------------

            if self._is_model_on_cooldown(
                model.provider,
                model.name,
            ):

                remaining = (
                    self._cooldown_remaining(
                        model.provider,
                        model.name,
                    )
                )

                debug_print(
                    "[AI ROUTER] Skipping model on cooldown:",
                    model.provider,
                    model.name,
                    f"({remaining}s)",
                )

                continue

            provider = self.get_provider(
                model.provider
            )

            # * ----------------------------------------------
            # * Provider not registered
            # * ----------------------------------------------

            if provider is None:

                debug_print(
                    "[AI ROUTER] Provider not registered:",
                    model.provider,
                )

                continue

            # * ----------------------------------------------
            # * Provider unavailable
            # * ----------------------------------------------

            if not provider.is_available():

                debug_print(
                    "[AI ROUTER] Skipping unavailable:",
                    model.provider,
                    model.name,
                )

                continue

            # * ----------------------------------------------
            # * Select model
            # * ----------------------------------------------

            request.model = model.name

            request.provider = model.provider

            debug_print(
                "[AI ROUTER] Trying:",
                model.provider,
                model.name,
            )

            # * ----------------------------------------------
            # * Generate
            # * ----------------------------------------------

            try:

                response = provider.generate(
                    request
                )

            except Exception as e:

                last_error = str(e)

                quota_error = self._is_quota_error(e, model.provider)

                if quota_error and model.provider.lower() == "gemini":
                    print(
                        "[AI ROUTER] Gemini quota exhausted:",
                        model.name,
                    )
                else:
                    print(
                        "[AI ROUTER] Provider exception:",
                        model.provider,
                        e,
                    )

                # * ------------------------------------------
                # * Quota/rate-limit protection
                # * ------------------------------------------

                if quota_error:

                    self._cooldown_model(
                        model.provider,
                        model.name,
                        e,
                    )

                continue

            # * ----------------------------------------------
            # * Success
            # * ----------------------------------------------

            if response.success:

                print(
                    "[AI ROUTER] Model used:",
                    response.provider or model.provider,
                    response.model or model.name,
                )

                debug_print(
                    "[AI ROUTER] Success:",
                    model.provider,
                    model.name,
                )

                return response

            # * ----------------------------------------------
            # * Provider returned failure
            # * ----------------------------------------------

            last_error = response.error

            print(
                "[AI ROUTER] Generation failed:",
                model.provider,
                model.name,
            )

            quota_error = self._is_quota_error(response.error, model.provider)

            if quota_error and model.provider.lower() == "gemini":
                print(
                    "[AI ROUTER] Gemini quota exhausted:",
                    model.name,
                )
            else:
                print(
                    "[AI ROUTER] Error:",
                    response.error,
                )

            # * ----------------------------------------------
            # * Quota/rate-limit protection
            # * ----------------------------------------------

            if quota_error:

                self._cooldown_model(
                    model.provider,
                    model.name,
                    response.error,
                )

            # * ----------------------------------------------
            # * Continue to next model
            # * ----------------------------------------------

            continue

        # * --------------------------------------------------
        # * Everything failed
        # * --------------------------------------------------

        return AIResponse(

            text="",

            provider="",

            model="",

            success=False,

            error=(
                last_error
                or
                "All AI providers failed."
            ),
        )

    # * ======================================================
    # * Streaming With Fallback
    # * ======================================================

    def stream(
        self,
        request: AIRequest,
    ):

        candidates = self._get_candidates(
            request
        )

        if not candidates:

            raise RuntimeError(
                "No AI models available for "
                f"capability: {request.capability}"
            )

        # * --------------------------------------------------
        # * Streaming generator
        # * --------------------------------------------------

        def generate_stream():

            last_error = None

            # * ----------------------------------------------
            # * Try every candidate in policy order
            # * ----------------------------------------------

            for model in candidates:

                # * ------------------------------------------
                # * Temporary cooldown
                # * ------------------------------------------

                if self._is_model_on_cooldown(
                    model.provider,
                    model.name,
                ):

                    remaining = (
                        self._cooldown_remaining(
                            model.provider,
                            model.name,
                        )
                    )

                    debug_print(
                        "[AI ROUTER] Streaming skip:",
                        model.provider,
                        model.name,
                        f"(cooldown {remaining}s)",
                    )

                    continue

                provider = self.get_provider(
                    model.provider
                )

                # * ------------------------------------------
                # * Provider not registered
                # * ------------------------------------------

                if provider is None:

                    debug_print(
                        "[AI ROUTER] Streaming provider "
                        "not registered:",
                        model.provider,
                    )

                    continue

                # * ------------------------------------------
                # * Provider unavailable
                # * ------------------------------------------

                if not provider.is_available():

                    debug_print(
                        "[AI ROUTER] Streaming skip:",
                        model.provider,
                        model.name,
                    )

                    continue

                # * ------------------------------------------
                # * Select provider/model
                # * ------------------------------------------

                request.model = model.name

                request.provider = model.provider

                debug_print(
                    "[AI ROUTER] Streaming:",
                    model.provider,
                    model.name,
                )

                # * ------------------------------------------
                # * Start provider stream
                # * ------------------------------------------

                try:

                    provider_stream = provider.stream(
                        request
                    )

                    received_text = False

                    # * --------------------------------------
                    # * Consume provider stream
                    # * --------------------------------------

                    for chunk in provider_stream:

                        # * ----------------------------------
                        # * Stop requested
                        # * ----------------------------------

                        if (
                            request.stop_event is not None
                            and request.stop_event.is_set()
                        ):

                            return

                        # * ----------------------------------
                        # ! Provider reported an error
                        # * ----------------------------------

                        if (
                            chunk.done
                            and
                            chunk.metadata.get(
                                "success"
                            ) is False
                        ):

                            last_error = (
                                chunk.metadata.get(
                                    "error"
                                )
                                or
                                "Streaming generation failed."
                            )

                            print(
                                "[AI ROUTER] Streaming failed:",
                                model.provider,
                                model.name,
                            )

                            quota_error = self._is_quota_error(
                                last_error,
                                model.provider,
                            )

                            if quota_error and model.provider.lower() == "gemini":
                                print(
                                    "[AI ROUTER] Gemini quota exhausted:",
                                    model.name,
                                )
                            else:
                                print(
                                    "[AI ROUTER] Error:",
                                    last_error,
                                )

                            # * ----------------------------------
                            # * Quota/rate-limit protection
                            # * ----------------------------------

                            if quota_error:

                                self._cooldown_model(
                                    model.provider,
                                    model.name,
                                    last_error,
                                )

                            # * ----------------------------------
                            # * If no text was produced, safely
                            # * try the next provider.
                            # * ----------------------------------

                            if not received_text:

                                break

                            # * ----------------------------------
                            # * Partial response already sent.
                            # ! Do not duplicate it with another
                            # * provider.
                            # * ----------------------------------

                            yield chunk

                            return

                        # * ----------------------------------
                        # * Normal chunk
                        # * ----------------------------------

                        if chunk.text:

                            received_text = True

                        yield chunk

                        # * ----------------------------------
                        # * Normal completion
                        # * ----------------------------------

                        if chunk.done:

                            print(
                                "[AI ROUTER] Model used:",
                                model.provider,
                                model.name,
                            )

                            return

                    # * --------------------------------------
                    # * Provider stream ended without an
                    # ! explicit error.
                    # * --------------------------------------

                    if received_text:

                        print(
                            "[AI ROUTER] Model used:",
                            model.provider,
                            model.name,
                        )

                        return

                except Exception as e:

                    last_error = str(e)

                    quota_error = self._is_quota_error(e, model.provider)

                    if quota_error and model.provider.lower() == "gemini":
                        print(
                            "[AI ROUTER] Gemini quota exhausted:",
                            model.name,
                        )
                    else:
                        print(
                            "[AI ROUTER] Streaming exception:",
                            model.provider,
                            e,
                        )

                    # * --------------------------------------
                    # * Quota/rate-limit protection
                    # * --------------------------------------

                    if quota_error:

                        self._cooldown_model(
                            model.provider,
                            model.name,
                            e,
                        )

                    continue

            # * ----------------------------------------------
            # * All providers failed
            # * ----------------------------------------------

            print(
                "[AI ROUTER] All streaming providers failed."
            )

            yield AIStreamChunk(

                text="",

                provider="",

                model="",

                done=True,

                metadata={
                    "success": False,
                    "error": (
                        last_error
                        or
                        "All AI streaming providers failed."
                    ),
                },
            )

        return generate_stream()
