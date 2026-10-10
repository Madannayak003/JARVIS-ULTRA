"""
JARVIS PRO
AI Core - Gemini Provider

Google Gemini implementation of the JARVIS AIProvider.

Supports:

- Full generation
- Streaming generation
- System instructions
- Model override
- Optional image inputs
- Stop-event interruption
"""

import ssl
import time
from pathlib import Path
from typing import Iterator, Optional

import httpx
import requests
from google import genai
from google.genai import types

from ai.core.schemas import (
    AIRequest,
    AIResponse,
    AIStreamChunk,
)
from core.diagnostics import debug_print

from ai.providers.base import AIProvider
from config.environment import get_env


def _is_quota_error(error) -> bool:
    text = str(error or "").lower()
    return any(
        marker in text
        for marker in (
            "429",
            "resource_exhausted",
            "quota exceeded",
            "quotaexceeded",
            "rate limit",
            "rate_limit",
            "too many requests",
        )
    )


_NETWORK_EXCEPTIONS = (
    requests.exceptions.RequestException,
    httpx.RequestError,
    ssl.SSLError,
    ConnectionError,
    TimeoutError,
)


def _network_error_details(error) -> tuple[str, str]:
    """Return a stable user-facing message and category for transport errors."""

    error_text = str(error or "")
    lowered = error_text.lower()

    if isinstance(error, ssl.SSLError) or any(
        marker in lowered
        for marker in (
            "ssl",
            "certificate verify failed",
            "tls",
            "handshake",
        )
    ):
        return (
            "Gemini SSL/TLS connection failed; trying another model.",
            "ssl",
        )

    if isinstance(error, (TimeoutError, httpx.TimeoutException)) or any(
        marker in lowered
        for marker in ("timed out", "timeout")
    ):
        return (
            "Gemini connection timed out; trying another model.",
            "timeout",
        )

    return (
        "Gemini network connection failed; trying another model.",
        "connection",
    )


class GeminiProvider(AIProvider):
    """
    Google Gemini implementation of AIProvider.

    Supports both normal text requests and
    multimodal requests containing images.
    """

    DEFAULT_MODEL = "gemini-3.6-flash"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
    ):

        self.api_key = api_key or get_env("GEMINI_API_KEY")

        self.model = model

        self._client = None

    # * ======================================================
    # * Provider Information
    # * ======================================================

    @property
    def name(self) -> str:

        return "gemini"

    # * ======================================================
    # * Client
    # * ======================================================

    def _get_client(self):

        if self._client is not None:

            return self._client

        if not self.api_key:

            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )

        self._client = genai.Client(
            api_key=self.api_key
        )

        return self._client

    # * ======================================================
    # * Availability
    # * ======================================================

    def is_available(self) -> bool:

        return bool(self.api_key)

    # * ======================================================
    # * Build Contents
    # * ======================================================

    def _build_contents(self, request: AIRequest):
        """
        Build Gemini contents.

        Existing text-only requests remain exactly
        as they were.

        When images are supplied, Gemini receives:

            image(s) + prompt
        """

        images = (
            request.images
            if request.images
            else []
        )

        # * --------------------------------------------------
        # * Existing text-only behavior
        # * --------------------------------------------------

        if not images:

            return request.prompt

        # * --------------------------------------------------
        # * Multimodal request
        # * --------------------------------------------------

        contents = []

        for image in images:

            contents.append(
                self._prepare_image(image)
            )

        contents.append(
            request.prompt
        )

        return contents

    # * ======================================================
    # * Prepare Image
    # * ======================================================

    def _prepare_image(self, image):
        """
        Convert supported image inputs into a Gemini
        compatible content object.

        Supported:

        - PIL.Image.Image
        - Gemini Part
        - bytes
        - pathlib.Path
        - string file path
        """

        # * --------------------------------------------------
        # * Already a Gemini Part / supported SDK object
        # * --------------------------------------------------

        if isinstance(
            image,
            types.Part,
        ):

            return image

        # * --------------------------------------------------
        # * PIL Image
        # * --------------------------------------------------

        try:

            from PIL import Image

            if isinstance(
                image,
                Image.Image,
            ):

                return image

        except ImportError:

            pass

        # * --------------------------------------------------
        # * Raw bytes
        # * --------------------------------------------------

        if isinstance(
            image,
            bytes,
        ):

            return types.Part.from_bytes(
                data=image,
                mime_type="image/png",
            )

        # * --------------------------------------------------
        # * File path
        # * --------------------------------------------------

        if isinstance(
            image,
            (str, Path),
        ):

            path = Path(image)

            if not path.exists():

                raise FileNotFoundError(
                    f"Image file not found: {path}"
                )

            suffix = (
                path.suffix.lower()
            )

            mime_types = {

                ".jpg": "image/jpeg",

                ".jpeg": "image/jpeg",

                ".png": "image/png",

                ".webp": "image/webp",

                ".gif": "image/gif",

            }

            mime_type = mime_types.get(
                suffix,
                "image/png",
            )

            with open(
                path,
                "rb",
            ) as file:

                image_bytes = file.read()

            return types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type,
            )

        # * --------------------------------------------------
        # * Unsupported input
        # * --------------------------------------------------

        raise TypeError(
            "Unsupported Gemini image input: "
            f"{type(image).__name__}"
        )

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

            config = None

            if request.system_prompt:

                config = (
                    types.GenerateContentConfig(
                        system_instruction=(
                            request.system_prompt
                        )
                    )
                )

            contents = (
                self._build_contents(
                    request
                )
            )

            response = (
                client.models.generate_content(

                    model=model,

                    contents=contents,

                    config=config,
                )
            )

            text = (
                response.text
                or ""
            )

            if not text.strip():

                return AIResponse(

                    text="",

                    provider=self.name,

                    model=model,

                    success=False,

                    error="Gemini returned an empty response.",

                    metadata={
                        "response": response,

                        "multimodal": bool(
                            request.images
                        ),
                    },
                )

            return AIResponse(

                text=text,

                provider=self.name,

                model=model,

                success=True,

                metadata={
                    "response": response,
                    "multimodal": bool(
                        request.images
                    ),
                },
            )

        except _NETWORK_EXCEPTIONS as e:

            message, error_type = _network_error_details(e)

            print(
                "[GEMINI WARNING]",
                message,
                "provider endpoint.",
            )

            return AIResponse(

                text="",

                provider=self.name,

                model=model,

                success=False,

                error=message,

                metadata={
                    "error_type": error_type,
                    "exception_type": type(e).__name__,
                },
            )

        except Exception as e:

            if not _is_quota_error(e):
                print(
                    f"[GEMINI ERROR] {e}"
                )

            return AIResponse(

                text="",

                provider=self.name,

                model=model,

                success=False,

                error=str(e),

                metadata={
                    "error_type": (
                        type(e).__name__
                    )
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

            config = None

            if request.system_prompt:

                config = (
                    types.GenerateContentConfig(
                        system_instruction=(
                            request.system_prompt
                        )
                    )
                )

            contents = (
                self._build_contents(
                    request
                )
            )

            # * ==================================================
            # ! GEMINI REQUEST DEBUG
            # * ==================================================

            debug_print(
                "[GEMINI DEBUG] prompt length:",
                len(request.prompt or "")
            )

            debug_print(
                "[GEMINI DEBUG] system prompt length:",
                len(request.system_prompt or "")
            )

            debug_print(
                "[GEMINI DEBUG] capability:",
                request.capability
            )

            debug_print(
                "[GEMINI DEBUG] model:",
                request.model
            )

            debug_print(
                "[GEMINI DEBUG] metadata keys:",
                list((request.metadata or {}).keys())
            )

            # * ==================================================
            # * STREAM TIMING
            # * ==================================================

            stream_start = time.perf_counter()

            debug_print(
                f"[GEMINI STREAM] Request started: {model}"
            )

            client_start = time.perf_counter()

            client = self._get_client()

            debug_print(
                "[GEMINI STREAM] Client ready:",
                f"{time.perf_counter() - client_start:.3f}s"
            )

            api_start = time.perf_counter()

            response_stream = (
                client.models.generate_content_stream(

                    model=model,

                    contents=contents,

                    config=config,
                )
            )

            debug_print(
                "[GEMINI STREAM] API stream created:",
                f"{time.perf_counter() - api_start:.3f}s"
            )

            first_text_time = None

            for chunk in response_stream:

                # * ------------------------------------------
                # * Stop requested
                # * ------------------------------------------

                if (
                    request.stop_event is not None
                    and request.stop_event.is_set()
                ):

                    debug_print(
                        "[GEMINI STREAM] Interrupted"
                    )

                    break

                text = getattr(
                    chunk,
                    "text",
                    "",
                ) or ""

                if text:

                    # * --------------------------------------
                    # * First text timing
                    # * --------------------------------------

                    if first_text_time is None:

                        first_text_time = (
                            time.perf_counter()
                        )

                        debug_print(
                            "[GEMINI STREAM] "
                            f"FIRST TEXT: "
                            f"{first_text_time - stream_start:.3f}s"
                        )

                    debug_print(
                        "[GEMINI STREAM] CHUNK:",
                        repr(text),
                    )

                    yield AIStreamChunk(

                        text=text,

                        provider=self.name,

                        model=model,

                        done=False,

                        metadata={
                            "response": chunk,
                        },
                    )

        except _NETWORK_EXCEPTIONS as e:

            message, error_type = _network_error_details(e)

            print(
                "[GEMINI STREAM WARNING]",
                message,
                "provider endpoint.",
            )

            yield AIStreamChunk(

                text="",

                provider=self.name,

                model=model,

                done=True,

                metadata={
                    "error": message,
                    "success": False,
                    "error_type": error_type,
                    "exception_type": type(e).__name__,
                },
            )

            return

        except Exception as e:

            if not _is_quota_error(e):
                print(
                    f"[GEMINI STREAM ERROR] {e}"
                )

            yield AIStreamChunk(

                text="",

                provider=self.name,

                model=model,

                done=True,

                metadata={

                    "error": str(e),

                    "success": False,

                    "error_type": (
                        type(e).__name__
                    ),

                },
            )

            return

        # * ==================================================
        # * NORMAL COMPLETION
        # * ==================================================

        total_time = (
            time.perf_counter()
            - stream_start
        )

        debug_print(
            "[GEMINI STREAM] COMPLETE:",
            f"{total_time:.3f}s"
        )

        yield AIStreamChunk(

            text="",

            provider=self.name,

            model=model,

            done=True,

            metadata={

                "success": True,

            },
        )
