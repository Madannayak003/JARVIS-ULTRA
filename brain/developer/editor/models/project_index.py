"""
JARVIS PRO
Developer Editor

Project Index
"""

from dataclasses import dataclass, field


@dataclass
class ProjectIndex:
    """
    Stores an index of the entire project.

    Used by the Target Locator to intelligently
    locate files, functions, classes and imports.
    """

    # * -------------------------------------
    # * All editable project files
    # * -------------------------------------

    files: list[str] = field(
        default_factory=list,
    )

    # * -------------------------------------
    # * function_name -> files
    # * Example:
    #
    # * {
    # * "login": ["src/auth.py"]
    # * }
    # * -------------------------------------

    functions: dict[str, list[str]] = field(
        default_factory=dict,
    )

    # * -------------------------------------
    # * class_name -> files
    # * -------------------------------------

    classes: dict[str, list[str]] = field(
        default_factory=dict,
    )

    # * -------------------------------------
    # * imported_module -> files
    # * -------------------------------------

    imports: dict[str, list[str]] = field(
        default_factory=dict,
    )