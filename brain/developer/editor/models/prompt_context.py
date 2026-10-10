"""
JARVIS PRO
Developer Editor

Prompt Context
"""

from dataclasses import dataclass

from brain.developer.editor.models.edit_request import (
    EditRequest,
)


@dataclass
class PromptContext:

    request: EditRequest