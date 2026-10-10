"""
Analysis Result Model
"""

from dataclasses import dataclass
from typing import Optional

from brain.developer.enums import (
    Intent,
    Language,
    Framework,
    ProjectType,
    Workspace,
    Board,
    Runtime,
)


@dataclass(slots=True)
class AnalysisResult:
    """
    Result produced by the Analyzer.
    """

    # * Original user request
    user_request: str = ""
    
    intent: Optional[Intent] = None

    language: Optional[Language] = None

    framework: Optional[Framework] = None

    project_type: Optional[ProjectType] = None

    workspace: Optional[Workspace] = None

    board: Optional[Board] = None

    runtime: Optional[Runtime] = None