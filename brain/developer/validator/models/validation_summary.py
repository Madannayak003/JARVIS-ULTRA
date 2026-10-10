"""
JARVIS PRO
Developer Validator

Validation Summary
"""

from dataclasses import dataclass


@dataclass(slots=True)
class ValidationSummary:

    structure: bool = False

    files: bool = False

    language: bool = False

    framework: bool = False

    dependencies: bool = False

    project: bool = False

    content: bool = False