"""
JARVIS PRO
AI Core - OpenAI Provider

OpenAI / GPT implementation of the JARVIS AIProvider.

Supports:
- Full generation
- Streaming generation
- System prompts
- Model override
- Stop-event interruption
"""

import ssl
from typing import Iterator, Optional

import httpx
from openai import OpenAI
import truststore

from ai.core.schemas import (
    AIRequest,
    AIResponse,
    AIStreamChunk,
)

from ai.providers.base import AIProvider
from config.environment import get_env


class OpenAIProvider(AIProvider):
    """
    OpenAI implementation of AIProvider.
    """

    DEFAULT_MODEL = "gpt-5.4-mini"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
    ):

        self.api_key = api_key or get_env("OPENAI_API_KEY")

        self.model = model

        self._client = None

    def _error_details(self, error) -> str:
        """Return concise OpenAI diagnostics without exposing credentials."""

        status = getattr(error, "status_code", None)
        body = getattr(error, "body", None)
        body = body if isinstance(body, dict) else {}

        detail = body.get("message") or str(error)
        error_code = body.get("code") or body.get("type")

        if error_code:
            detail = f"{error_code}: {detail}"

        if status:
            detail = f"HTTP {status} - {detail}"

        if self.api_key:
            detail = detail.replace(self.api_key, "[REDACTED]")

        return detail

    # * ======================================================
    # * Provider Information
    # * ======================================================

    @property
    def name(self) -> str:

        return "openai"

    # * ======================================================
    # * Client
    # * ======================================================

    def _get_client(self):

        if self._client is not None:

            return self._client

        if not self.api_key:

            raise RuntimeError(
                "OPENAI_API_KEY is not configured."
            )

        http_client = httpx.Client(
            verify=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        )

        self._client = OpenAI(
            api_key=self.api_key,
            http_client=http_client,
        )

        return self._client

    # * ======================================================
    # * Availability
    # * ======================================================

    def is_available(self) -> bool:

        return bool(self.api_key)

    # * ======================================================
    # * Full Generation
    # * ======================================================

    def generate(
        self,
        request: AIRequest,
    ) -> AIResponse:

        model = (
            request.model
            or self.model
        )

        try:

            client = self._get_client()

            messages = []

            # * --------------------------------------------------
            # * System message
            # * --------------------------------------------------

            if request.system_prompt:

                messages.append({

                    "role": "system",

                    "content": (
                        request.system_prompt
                    ),

                })

            # * --------------------------------------------------
            # * User message
            # * --------------------------------------------------

            messages.append({

                "role": "user",

                "content": request.prompt,

            })

            response = client.chat.completions.create(

                model=model,

                messages=messages,

            )

            text = (
                response.choices[0]
                .message
                .content
                or ""
            )

            return AIResponse(

                text=text,

                provider=self.name,

                model=model,

                success=True,

                metadata={
                    "response": response,
                },
            )

        except Exception as e:

            error_details = self._error_details(e)

            print(
                f"[OPENAI ERROR] {error_details}"
            )

            return AIResponse(

                text="",

                provider=self.name,

                model=model,

                success=False,

                error=error_details,

                metadata={
                    "error_type": (
                        type(e).__name__
                    ),
                    "status_code": getattr(
                        e,
                        "status_code",
                        None,
                    ),
                },
            )

    # * ======================================================
    # * Streaming
    # * ======================================================

    def stream(
        self,
        request: AIRequest,
    ) -> Iterator[AIStreamChunk]:

        model = (
            request.model
            or self.model
        )

        try:

            client = self._get_client()

            messages = []

            # * --------------------------------------------------
            # * System message
            # * --------------------------------------------------

            if request.system_prompt:

                messages.append({

                    "role": "system",

                    "content": (
                        request.system_prompt
                    ),

                })

            # * --------------------------------------------------
            # * User message
            # * --------------------------------------------------

            messages.append({

                "role": "user",

                "content": request.prompt,

            })

            response_stream = (
                client.chat.completions.create(

                    model=model,

                    messages=messages,

                    stream=True,

                )
            )

            for chunk in response_stream:

                # * ----------------------------------------------
                # * Stop requested
                # * ----------------------------------------------

                if (
                    request.stop_event is not None
                    and request.stop_event.is_set()
                ):

                    print(
                        "\n[OPENAI STREAM] Interrupted"
                    )

                    break

                if not chunk.choices:

                    continue

                delta = (
                    chunk.choices[0]
                    .delta
                    .content
                    or ""
                )

                if delta:

                    yield AIStreamChunk(

                        text=delta,

                        provider=self.name,

                        model=model,

                        done=False,

                        metadata={
                            "response": chunk,
                        },
                    )

        except Exception as e:

            error_details = self._error_details(e)

            print(
                f"[OPENAI STREAM ERROR] {error_details}"
            )

            yield AIStreamChunk(

                text="",

                provider=self.name,

                model=model,

                done=True,

                metadata={
                    "error": error_details,

                    "success": False,

                    "error_type": (
                        type(e).__name__
                    ),

                    "status_code": getattr(
                        e,
                        "status_code",
                        None,
                    ),
                },
            )

            return

        # * --------------------------------------------------
        # * Normal completion
        # * --------------------------------------------------

        yield AIStreamChunk(

            text="",

            provider=self.name,

            model=model,

            done=True,

            metadata={
                "success": True,
            },
        )
