"""
JARVIS PRO
Developer

Developer Context
"""

from dataclasses import dataclass
from typing import Optional

from brain.developer.models.analysis_result import AnalysisResult
from brain.developer.planner.models.execution_plan import ExecutionPlan
from brain.developer.prompt_builder.models.prompt_result import PromptResult
from brain.developer.validator.models.validation_result import (
    ValidationResult,
)
from brain.developer.generator.models.generated_project import (
    GeneratedProject,
)
from brain.developer.workspace.models.workspace_result import (
    WorkspaceResult,
)

from brain.developer.repair.models.repair_result import (
    RepairResult,
)

@dataclass(slots=True)
class DeveloperContext:
    """
    Shared context that flows through
    the entire Developer pipeline.
    """

    # * -----------------------------------
    # * User
    # * -----------------------------------

    user_request: str

    # * -----------------------------------
    # * Phase 2
    # * -----------------------------------

    analysis: Optional[AnalysisResult] = None

    # * -----------------------------------
    # * Phase 3
    # * -----------------------------------

    execution_plan: Optional[ExecutionPlan] = None

    # * -----------------------------------
    # * Phase 4
    # * -----------------------------------

    prompt_result: Optional[PromptResult] = None

    # * -----------------------------------
    # * Phase 5
    # * -----------------------------------

    generated_project: Optional[GeneratedProject] = None

    # * -----------------------------------
    # * Phase 6
    # * -----------------------------------

    validation_result: Optional[ValidationResult] = None

    # * -----------------------------------
    # * Phase 7
    # * -----------------------------------

    workspace_result: Optional[WorkspaceResult] = None
    
    # * -----------------------------------
    # * Phase 7.1
    # * -----------------------------------

    repair_result: Optional[RepairResult] = None
    