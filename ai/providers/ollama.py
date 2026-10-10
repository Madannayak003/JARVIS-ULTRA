"""
JARVIS PRO
AI Core - Ollama Provider

Provides:
- Full Ollama generation
- Streaming Ollama generation
- Stop-event interruption
"""

import json
from typing import Iterator, Optional

import requests

from ai.core.schemas import (
    AIRequest,
    AIResponse,
    AIStreamChunk,
)

from ai.providers.base import AIProvider
from config.environment import get_env


class OllamaProvider(AIProvider):
    """
    Ollama implementation of the JARVIS AIProvider.
    """

    DEFAULT_URL = "http://127.0.0.1:11434/api/generate"

    DEFAULT_MODEL = "jarvis"

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        url: Optional[str] = None,
    ):

        self.model = model
        self.url = (
            url
            if url is not None
            else get_env("OLLAMA_API_URL", self.DEFAULT_URL)
        )

    # * ======================================================
    # * Provider Information
    # * ======================================================

    @property
    def name(self) -> str:

        return "ollama"

    # * ======================================================
    # * Availability
    # * ======================================================

    def is_available(self) -> bool:

        try:

            base_url = self.url.split("/api/", 1)[0].rstrip("/")
            response = requests.get(
                f"{base_url}/api/tags",
                timeout=3,
            )

            return response.ok

        except requests.RequestException:

            return False

    # * ======================================================
    # * Full Generation
    # * ======================================================

    def generate(
        self,
        request: AIRequest,
    ) -> AIResponse:

        model = request.model or self.model

        try:

            response = requests.post(

                self.url,

                json={
                    "model": model,

                    "system": request.system_prompt,

                    "prompt": request.prompt,

                    "stream": False,
                },

                timeout=(10, 300),
            )

            response.raise_for_status()

            data = response.json()

            text = data.get(
                "response",
                "",
            )

            return AIResponse(

                text=text,

                provider=self.name,

                model=model,

                success=True,

                metadata={
                    "done": data.get(
                        "done",
                        True,
                    )
                },
            )

        except requests.exceptions.ReadTimeout as e:

            return AIResponse(

                text="",

                provider=self.name,

                model=model,

                success=False,

                error="Ollama generation timed out.",

                metadata={
                    "error_type": "timeout",
                    "exception": str(e),
                },
            )

        except requests.exceptions.RequestException as e:

            return AIResponse(

                text="",

                provider=self.name,

                model=model,

                success=False,

                error=str(e),

                metadata={
                    "error_type": "connection",
                },
            )

        except Exception as e:

            return AIResponse(

                text="",

                provider=self.name,

                model=model,

                success=False,

                error=str(e),

                metadata={
                    "error_type": "unknown",
                },
            )

    # * ======================================================
    # * Streaming
    # * ======================================================

    def stream(
        self,
        request: AIRequest,
    ) -> Iterator[AIStreamChunk]:

        model = request.model or self.model

        response = None

        try:

            response = requests.post(

                self.url,

                json={
                    "model": model,

                    "system": request.system_prompt,

                    "prompt": request.prompt,

                    "stream": True,
                },

                stream=True,

                timeout=(10, None),
            )

            response.raise_for_status()

            for line in response.iter_lines():

                # * ------------------------------------------
                # * Stop requested
                # * ------------------------------------------

                if (
                    request.stop_event is not None
                    and request.stop_event.is_set()
                ):

                    print(
                        "\n[OLLAMA STREAM] Interrupted"
                    )

                    break

                if not line:

                    continue

                try:

                    chunk = json.loads(
                        line.decode("utf-8")
                    )

                except (
                    json.JSONDecodeError,
                    UnicodeDecodeError,
                ):

                    continue

                text = chunk.get(
                    "response",
                    "",
                )

                done = chunk.get(
                    "done",
                    False,
                )

                yield AIStreamChunk(

                    text=text,

                    provider=self.name,

                    model=model,

                    done=done,

                    metadata=chunk,
                )

                if done:

                    break

        except requests.exceptions.RequestException as e:

            print(
                f"[OLLAMA STREAM ERROR] {e}"
            )

            yield AIStreamChunk(

                text="",

                provider=self.name,

                model=model,

                done=True,

                metadata={
                    "error": str(e),
                    "success": False,
                },
            )

        finally:

            if response is not None:

                response.close()
