"""
JARVIS PRO
Developer

Custom Exceptions
"""


class DeveloperError(Exception):
    """Base Developer exception."""


class ConfigurationError(DeveloperError):
    """Configuration error."""


class AnalysisError(DeveloperError):
    """Analysis error."""


class PlanningError(DeveloperError):
    """Planning error."""


class GenerationError(DeveloperError):
    """Generation error."""


class ValidationError(DeveloperError):
    """Validation error."""


class WorkspaceError(DeveloperError):
    """Workspace error."""