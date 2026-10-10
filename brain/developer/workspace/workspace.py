"""
JARVIS PRO
Developer Workspace

Workspace Engine
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from brain.developer.context import DeveloperContext

from brain.developer.workspace.models.workspace_result import (
    WorkspaceResult,
)

from brain.developer.workspace.builders.project_builder import (
    ProjectBuilder,
)

from brain.developer.workspace.builders.folder_builder import (
    FolderBuilder,
)

from brain.developer.workspace.builders.file_builder import (
    FileBuilder,
)

from brain.developer.workspace.builders.workspace_resolver import (
    WorkspaceResolver,
)


class Workspace:
    """
    Main Workspace Engine.

    Creates the generated project on disk.
    """

    def __init__(self):
        
        self.workspace_resolver = WorkspaceResolver()

        self.project_builder = ProjectBuilder()

        self.folder_builder = FolderBuilder()

        self.file_builder = FileBuilder()

    # * -----------------------------------------------------

    def create(
        self,
        context: "DeveloperContext",
    ) -> WorkspaceResult:
        """
        Create the generated project.
        """

        project = context.generated_project
        
        # * -------------------------------------
        # * Resolve Workspace
        # * -------------------------------------

        output_directory = self.workspace_resolver.resolve(

            context.analysis.workspace

        )

        # * -------------------------------------
        # * Create Project
        # * -------------------------------------

        result = self.project_builder.build(

            project,

            output_directory,

        )

        # * -------------------------------------
        # * Create Folders
        # * -------------------------------------

        result = self.folder_builder.build(

            project,

            result,

        )

        # * -------------------------------------
        # * Create Files
        # * -------------------------------------

        result = self.file_builder.build(

            project,

            result,

        )

        # * -------------------------------------
        # * Final Status
        # * -------------------------------------

        result.success = (

            len(result.errors) == 0

        )

        # * -------------------------------------
        # * Store in Context
        # * -------------------------------------

        context.workspace_result = result

        return result