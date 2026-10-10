"""
JARVIS PRO
Developer Workspace

Project Builder
"""

from pathlib import Path

from brain.developer.generator.models.generated_project import (
    GeneratedProject,
)

from brain.developer.workspace.models.workspace_result import (
    WorkspaceResult,
)

from brain.developer.workspace.builders.project_name_resolver import (
    ProjectNameResolver,
)


class ProjectBuilder:
    """
    Creates the root project directory.
    """

    def __init__(self):

        self.name_resolver = ProjectNameResolver()

    # * -----------------------------------------------------

    def build(
        self,
        project: GeneratedProject,
        output_directory: str,
    ) -> WorkspaceResult:
        """
        Create the root project folder.
        """

        result = WorkspaceResult()

        # * -------------------------------------
        # * Resolve Project Name
        # * -------------------------------------

        project_name = self.name_resolver.resolve(
            project,
            Path(output_directory),
        )

        # * -------------------------------------
        # * Project Path
        # * -------------------------------------

        project_path = (

            Path(output_directory)

            / project_name

        )

        project_path.mkdir(

            parents=True,

            exist_ok=True,

        )

        # * -------------------------------------
        # * Result
        # * -------------------------------------

        result.success = True

        result.project_name = project_name

        result.project_path = str(project_path)

        return result