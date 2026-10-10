"""
JARVIS PRO
Developer Prompt Builder

Prompt Context
"""

from dataclasses import dataclass

from brain.developer.models.analysis_result import AnalysisResult
from brain.developer.planner.models.execution_plan import ExecutionPlan


@dataclass
class PromptContext:
    """
    Complete context required to build an LLM prompt.
    """

    user_request: str

    analysis: AnalysisResult

    execution_plan: ExecutionPlan
    