"""
JARVIS PRO
Developer Validator

Base Validator
"""

from abc import ABC, abstractmethod

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from brain.developer.context import DeveloperContext

from brain.developer.validator.models.validation_result import (
    ValidationResult,
)


class BaseValidator(ABC):
    """
    Base class for all validators.
    """

    @abstractmethod
    def validate(
        self,
        context: "DeveloperContext",
        result: ValidationResult,
    ) -> None:
        """
        Validate the generated project.

        Validators should update the supplied
        ValidationResult directly.
        """

        pass