from ai.core.service import ai_service
from ai.chat_prompt import get_chat_prompt

from brain import pipeline

from dataclasses import dataclass
from typing import Optional, Iterator


# * ==========================================================
# AI Chat Streaming Adapter
# * ==========================================================

def ai_chat_stream(
    system_prompt,
    prompt,
    stop_event=None,
):
    """
    Adapter between the new AIService streaming API
    and the existing Brain AIPipeline.
    """

    stream = ai_service.stream(

        prompt=prompt,

        system_prompt=system_prompt,

        capability="conversation",

        stop_event=stop_event,

    )

    for chunk in stream:

        if chunk.text:

            yield {
                "response": chunk.text,

                "provider": chunk.provider,

                "model": chunk.model,

                "done": chunk.done,
            }


# * ==========================================================
# * Chat Session
# * ==========================================================

@dataclass
class ChatSession:

    stream: Iterator

    is_developer: bool = False

    language: Optional[str] = None

    framework: Optional[str] = None

    project_type: Optional[str] = None


# * ==========================================================
# AI Chat Entry
# * ==========================================================

def ask_chat(
    question,
    stop_event=None,
):

    stream = pipeline.process_stream(

        user_input=question,

        stream_callback=ai_chat_stream,

        system_prompt=get_chat_prompt(),

        stop_event=stop_event

    )

    return ChatSession(

        stream=stream,

        is_developer=False,

        language=None,

        framework=None,

        project_type=None

    )
