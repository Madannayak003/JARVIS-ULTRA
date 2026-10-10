"""
JARVIS PRO
Developer Generator

Generated Project
"""

from dataclasses import dataclass, field

from brain.developer.generator.models.generated_file import GeneratedFile


@dataclass(slots=True)
class GeneratedProject:
    """
    Represents a complete generated project.
    """

    # * ---------------------------------------
    # * User Request
    # * ---------------------------------------

    user_request: str = ""

    # * ---------------------------------------
    # * Project Information
    # * ---------------------------------------

    project_name: str = ""

    name: str = ""

    project_type: str = ""

    language: str = ""

    framework: str = ""

    workspace: str = ""

    runtime: str = ""

    board: str = ""

    # * ---------------------------------------
    # * Generated Files
    # * ---------------------------------------

    files: list[GeneratedFile] = field(default_factory=list)

    # * ---------------------------------------
    # * Project Metadata
    # * ---------------------------------------

    entry_file: str = ""

    build_command: str = ""

    run_command: str = ""

    test_command: str = ""

    package_manager: str = ""

    output_directory: str = ""

    generated: bool = False

    confidence: float = 0.0

    # * ---------------------------------------
    # * Statistics
    # * ---------------------------------------

    file_count: int = 0

    created_files: int = 0

    created_folders: int = 0

    total_characters: int = 0

    # * ---------------------------------------
    # * Parser / Generator Status
    # * ---------------------------------------

    errors: list[str] = field(default_factory=list)

    warnings: list[str] = field(default_factory=list)

    # * ---------------------------------------
    # * Extra Metadata
    # * ---------------------------------------

    metadata: dict = field(default_factory=dict)