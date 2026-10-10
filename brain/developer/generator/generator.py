"""
JARVIS PRO
Developer Generator

Generator Engine
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from brain.developer.context import DeveloperContext

from brain.developer.generator.models.generated_project import GeneratedProject
from brain.developer.generator.providers.ollama_provider import OllamaProvider
from brain.developer.generator.parsers.response_parser import ResponseParser
from brain.developer.generator.metadata.metadata_builder import (
    MetadataBuilder,
)


class Generator:
    """
    Main Generator Engine.

    Responsible only for orchestrating
    the generation pipeline.
    """

    def __init__(self):

        self.provider = OllamaProvider()

        self.parser = ResponseParser()

        self.metadata_builder = MetadataBuilder()

    # * -----------------------------------------------------

    def generate(
        self,
        context: "DeveloperContext",
    ) -> GeneratedProject:
        """
        Generate a project from the PromptBuilder output.
        """

        # * ---------------------------------------
        # * Generate AI Response
        # * ---------------------------------------

        response = self.provider.generate(
            context.prompt_result
        )

        # * ---------------------------------------
        # AI Generation Failed
        # * ---------------------------------------

        if not response:

            project = GeneratedProject()

            project.generated = False

            project.errors.append(

                "AI generation failed."

            )

            context.generated_project = project

            return project

        # * ---------------------------------------
        # ! Debug (Phase 6)
        # * ---------------------------------------


        # * ---------------------------------------
        # * Parse Response
        # * ---------------------------------------

        project = self.parser.parse(response)

        # * ---------------------------------------
        # * Basic Project Information
        # * ---------------------------------------

        analysis = context.analysis

        project.user_request = context.user_request

        project.language = str(analysis.language)

        project.framework = str(analysis.framework)

        project.workspace = str(analysis.workspace)

        project.project_type = str(analysis.project_type)

        project.runtime = str(analysis.runtime)

        project.board = str(analysis.board)

        # * ---------------------------------------
        # * Statistics
        # * ---------------------------------------

        project.file_count = len(project.files)

        project.total_characters = sum(

            len(file.content)

            for file in project.files

        )

        # * ---------------------------------------
        # * Generation Status
        # * ---------------------------------------

        project.generated = bool(project.files)

        if not project.generated:

            project.errors.append(
                "No project files were generated."
            )

        # * ---------------------------------------
        # * Build Metadata
        # * ---------------------------------------

        self.metadata_builder.build(project)

        # * ---------------------------------------
        # * Store Context
        # * ---------------------------------------
        
        print("\n========== PROJECT METADATA ==========")
        print("Language      :", project.language)
        print("Entry File    :", project.entry_file)
        print("Run Command   :", project.run_command)
        print("Build Command :", project.build_command)
        print("======================================\n")

        context.generated_project = project

        return project