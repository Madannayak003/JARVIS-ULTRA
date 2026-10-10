"""
JARVIS PRO
Developer Workspace

Folder Builder
"""

from pathlib import Path

from brain.developer.generator.models.generated_project import (
    GeneratedProject,
)

from brain.developer.workspace.models.workspace_result import (
    WorkspaceResult,
)

from brain.developer.workspace.models.created_folder import (
    CreatedFolder,
)

from brain.developer.workspace.writers.folder_writer import (
    FolderWriter,
)


class FolderBuilder:
    """
    Creates all required project folders.
    """

    def __init__(self):

        self.writer = FolderWriter()

    # * -----------------------------------------------------

    def build(
        self,
        project: GeneratedProject,
        result: WorkspaceResult,
    ) -> WorkspaceResult:
        """
        Create every folder required by the project.
        """

        folders = set()

        # * -------------------------------------
        # * Collect Folder Paths
        # * -------------------------------------

        for generated_file in project.files:

            parent = Path(generated_file.path).parent

            if str(parent) != ".":

                folders.add(str(parent))

        # * -------------------------------------
        # * Create Folders
        # * -------------------------------------

        for folder in sorted(folders):

            full_path = Path(result.project_path) / folder

            success = self.writer.create(str(full_path))

            created = CreatedFolder(

                name=full_path.name,

                path=str(full_path),

                created=success,

            )

            result.folders.append(created)

        # * -------------------------------------
        # * Statistics
        # * -------------------------------------

        result.folder_count = len(result.folders)

        return result