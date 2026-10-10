"""
JARVIS PRO
Developer Repair

Repair Prompt
"""

from dataclasses import dataclass


@dataclass(slots=True)
class RepairPrompt:
    """
    Prompt sent to the AI
    for repairing a project.
    """

    system_prompt: str = ""

    user_prompt: str = ""