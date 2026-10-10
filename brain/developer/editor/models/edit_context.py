"""
JARVIS PRO
Developer Editor

Edit Context
"""

from dataclasses import dataclass

from brain.developer.editor.models.edit_request import EditRequest
from brain.developer.editor.models.edit_result import EditResult


@dataclass
class EditContext:
    """
    Context shared across the Editor pipeline.
    """

    user_request: str = ""

    project_path: str = ""

    edit_request: EditRequest | None = None

    analysis = None

    plan = None

    prompt = None

    response: str = ""

    result: EditResult | None = None