"""
JARVIS PRO
AI Core - Grok Provider

xAI's OpenAI-compatible chat completions provider.
"""

import ssl
from typing import Iterator, Optional

import httpx
from openai import OpenAI
import truststore

from ai.core.schemas import AIRequest, AIResponse, AIStreamChunk
from ai.providers.base import AIProvider
from config.environment import get_env


class GrokProvider(AIProvider):
    """Grok implementation of the existing JARVIS AIProvider interface."""

    BASE_URL = "https://api.x.ai/v1"
    DEFAULT_MODEL = "grok-4.7"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
    ):
        self.api_key = api_key or get_env("XAI_API_KEY")
        self.model = model
        self._client = None

    @property
    def name(self) -> str:
        return "grok"

    def _get_client(self):
        if self._client is not None:
            return self._client

        if not self.api_key:
            raise RuntimeError("XAI_API_KEY is not configured.")

        http_client = httpx.Client(
            verify=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        )
        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.BASE_URL,
            http_client=http_client,
        )
        return self._client

    def is_available(self) -> bool:
        return bool(self.api_key)

    def _messages(self, request: AIRequest):
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        return messages

    def _error_details(self, error) -> str:
        """Return a safe, concise error suitable for fallback handling."""

        status = getattr(error, "status_code", None)
        text = str(error or "").lower()

        if status in (401, 403) or "authentication" in text or "api key" in text:
            return f"Grok authentication failed{f' (HTTP {status})' if status else ''}."
        if status == 429 or "rate limit" in text or "too many requests" in text:
            return "Grok rate limit reached (HTTP 429)."
        if "timeout" in text or "timed out" in text:
            return "Grok request timed out."
        if status:
            return f"Grok API request failed (HTTP {status})."
        return "Grok API request failed."

    def generate(self, request: AIRequest) -> AIResponse:
        model = request.model or self.model
        try:
            response = self._get_client().chat.completions.create(
                model=model,
                messages=self._messages(request),
            )
            text = response.choices[0].message.content or ""
            return AIResponse(
                text=text,
                provider=self.name,
                model=model,
                success=True,
                metadata={"response": response},
            )
        except Exception as error:
            return AIResponse(
                text="",
                provider=self.name,
                model=model,
                success=False,
                error=self._error_details(error),
                metadata={
                    "error_type": type(error).__name__,
                    "status_code": getattr(error, "status_code", None),
                },
            )

    def stream(self, request: AIRequest) -> Iterator[AIStreamChunk]:
        model = request.model or self.model
        try:
            response_stream = self._get_client().chat.completions.create(
                model=model,
                messages=self._messages(request),
                stream=True,
            )
            for chunk in response_stream:
                if request.stop_event is not None and request.stop_event.is_set():
                    return
                if not chunk.choices:
                    continue
                text = chunk.choices[0].delta.content or ""
                if text:
                    yield AIStreamChunk(
                        text=text,
                        provider=self.name,
                        model=model,
                        done=False,
                        metadata={"response": chunk},
                    )
        except Exception as error:
            yield AIStreamChunk(
                text="",
                provider=self.name,
                model=model,
                done=True,
                metadata={
                    "error": self._error_details(error),
                    "success": False,
                    "error_type": type(error).__name__,
                    "status_code": getattr(error, "status_code", None),
                },
            )
            return

        yield AIStreamChunk(
            text="",
            provider=self.name,
            model=model,
            done=True,
            metadata={"success": True},
        )
