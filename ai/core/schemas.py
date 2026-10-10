"""
JARVIS PRO
AI Core - Schemas

Common data contracts shared by:
- Ollama
- Google Gemini
- OpenAI / GPT
- AI Router
- AI Service
- JARVIS consumers
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, Optional

# * ==========================================================
# AI Request
# * ==========================================================

@dataclass
class AIRequest:
    """
    Standard request sent to the AI Core.

    Supports:
    - Text-only requests
    - Optional image inputs for vision-capable models

    Existing text-only callers remain fully compatible.
    """

    prompt: str

    system_prompt: str = ""

    capability: str = "conversation"

    provider: Optional[str] = None

    model: Optional[str] = None

    stream: bool = False

    stop_event: Any = None

    output_format: str = "text"

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    # * ------------------------------------------------------
    # * Optional multimodal input
    # * ------------------------------------------------------

    images: list[Any] = field(
        default_factory=list
    )


# * ==========================================================
# AI Response
# * ==========================================================

@dataclass
class AIResponse:
    """
    Standard non-streaming AI response.
    """

    text: str = ""

    provider: str = ""

    model: str = ""

    success: bool = True

    error: Optional[str] = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


# * ==========================================================
# AI Stream Chunk
# * ==========================================================

@dataclass
class AIStreamChunk:
    """
    Standard streaming chunk.

    Providers such as Ollama, Gemini and OpenAI
    can have different raw streaming formats.

    JARVIS converts them into this common format.
    """

    text: str = ""

    provider: str = ""

    model: str = ""

    done: bool = False

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


# * ==========================================================
# AI Error
# * ==========================================================

@dataclass
class AIError:
    """
    Standard AI error information.
    """

    message: str

    provider: str = ""

    model: str = ""

    error_type: str = "unknown"

    retryable: bool = False

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )