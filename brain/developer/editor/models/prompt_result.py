"""
JARVIS PRO
Developer Editor

Prompt Result
"""

from dataclasses import dataclass


@dataclass
class PromptResult:

    system_prompt: str = ""

    user_prompt: str = ""

    prompt: str = ""