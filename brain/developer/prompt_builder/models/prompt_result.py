"""
JARVIS PRO
Developer Prompt Builder

Prompt Result
"""

from dataclasses import dataclass, field


@dataclass(slots=True)
class PromptResult:
    """
    Final prompt produced by the Prompt Builder.
    """

    system_prompt: str = ""

    user_prompt: str = ""

    prompt: str = ""

    metadata: dict = field(default_factory=dict)