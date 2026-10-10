"""
JARVIS PRO
Developer Repair

Repair Engine
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from brain.developer.context import DeveloperContext

from brain.developer.repair.repair_builder import (
    RepairBuilder,
)

from brain.developer.repair.repair_provider import (
    RepairProvider,
)

from brain.developer.repair.repair_parser import (
    RepairParser,
)

from brain.developer.repair.models.repair_result import (
    RepairResult,
)

from brain.developer.repair.prompt_builder import (
    RepairPromptBuilder,
)

from brain.developer.repair.merge_builder import (
    MergeBuilder,
)

from brain.developer.repair.local_file_builder import (
    LocalFileBuilder,
)

from brain.developer.generator.models.generated_project import (
    GeneratedProject,
)

from brain.developer.generator.metadata.metadata_builder import (
    MetadataBuilder,
)

class Repair:
    """
    Main Repair Engine.
    """

    def __init__(self):

        self.builder = RepairBuilder()

        self.provider = RepairProvider()

        self.parser = RepairParser()
        
        self.prompt_builder = RepairPromptBuilder()

        self.merger = MergeBuilder()
        
        self.local_builder = LocalFileBuilder()

        self.metadata_builder = MetadataBuilder()

    # * -----------------------------------------------------

    def repair(
        self,
        context: "DeveloperContext",
    ) -> RepairResult:

        # * Build repair request

        request = self.builder.build(context)
        
        # * -------------------------------------
        # * Generate standard files locally
        # * -------------------------------------

        generated_locally = []

        remaining = []

        for filename in request.missing_files:

            file = self.local_builder.build(filename)

            if file is None:

                remaining.append(filename)

            else:

                generated_locally.append(file)

        request.missing_files = remaining

        result = RepairResult()
        
        if generated_locally:

            local_project = GeneratedProject()

            local_project.files = generated_locally

            context.generated_project = self.merger.build(

                context.generated_project,

                local_project,

            )

        # * Nothing to repair

        if (

            not request.missing_files

            and

            not request.missing_folders

        ):

            result.success = True

            return result

        # * -------------------------------------
        # * Build Prompt
        # * -------------------------------------

        prompt = self.prompt_builder.build(

            request,

        )

        # * -------------------------------------
        # AI Response
        # * -------------------------------------

        response = self.provider.generate(

            prompt,

        )
        
        print("\n" + "=" * 80)
        print("RAW REPAIR RESPONSE")
        print("=" * 80)
        print(response)
        print("=" * 80)

        if not response:

            result.errors.append(

                "Repair generation failed."

            )

            return result

        # * -------------------------------------
        # * Parse Response
        # * -------------------------------------

        repaired_project = self.parser.parse(

            response,

        )
        
        print("\n========== REPAIR RESPONSE ==========")
        print(response)

        print("\n========== REPAIRED FILES ==========")

        for file in repaired_project.files:
            print(file.path)

        # * -------------------------------------
        # * Merge Files
        # * -------------------------------------

        context.generated_project = self.merger.build(

            context.generated_project,

            repaired_project,

        )

        # Repaired projects can start from an empty Generator result.
        # Restore the same project metadata normally populated by Generator
        # before the pipeline performs re-validation.
        project = context.generated_project
        analysis = context.analysis

        project.user_request = context.user_request
        project.language = str(analysis.language)
        project.framework = str(analysis.framework)
        project.workspace = str(analysis.workspace)
        project.project_type = str(analysis.project_type)
        project.runtime = str(analysis.runtime)
        project.board = str(analysis.board)

        self.metadata_builder.build(project)
        
        print("\n========== MERGED FILES ==========")

        for file in context.generated_project.files:
            print(file.path)
            
        print("======================================")

        result.files = repaired_project.files

        result.repaired_files = len(

            repaired_project.files

        )

        result.success = True

        return result