"""
JARVIS PRO
Prompt Builder

Responsibilities
----------------
✓ Build optimized prompts
✓ Inject relevant memories
✓ Inject conversation history
✓ Keep prompts compact
"""

from ai.memory_search import (
    search,
    format_memories
)

from core.context import get_history


# * ---------------------------------------
# * Conversation
# * ---------------------------------------

def build_conversation(limit=6):

    history = get_history()

    if not history:
        return ""

    text = ""

    for item in history[-limit:]:

        role = item["role"].capitalize()

        text += f"{role}: {item['text']}\n"

    return text.strip()


# * ---------------------------------------
# * Memory
# * ---------------------------------------

def build_memory(question):

    memories = search(question)

    return format_memories(memories)


# * ---------------------------------------
# * Prompt
# * ---------------------------------------

def build_prompt(question):

    memory = build_memory(question)

    conversation = build_conversation()

    prompt = ""

    if memory:

        prompt += (
            "Relevant Personal Memory\n"
            "------------------------\n"
        )

        prompt += memory

        prompt += "\n\n"

    if conversation:

        prompt += (
            "Recent Conversation\n"
            "-------------------\n"
        )

        prompt += conversation

        prompt += "\n\n"

    prompt += (
        f"User Question:\n"
        f"{question}\n\n"
    )

    prompt += (
        "Answer naturally.\n"
        "If relevant personal memory exists, use it.\n"
        "Do not invent facts.\n"
        "Do not reveal internal reasoning."
    )

    return prompt