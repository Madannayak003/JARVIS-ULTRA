"""
JARVIS PRO
Developer Workspace

File Builder
"""

from pathlib import Path

from brain.developer.generator.models.generated_project import (
    GeneratedProject,
)

from brain.developer.workspace.models.workspace_result import (
    WorkspaceResult,
)

from brain.developer.workspace.models.created_file import (
    CreatedFile,
)

from brain.developer.workspace.writers.file_writer import (
    FileWriter,
)


class FileBuilder:
    """
    Creates every generated file.
    """

    def __init__(self):

        self.writer = FileWriter()

    # * -----------------------------------------------------

    def build(
        self,
        project: GeneratedProject,
        result: WorkspaceResult,
    ) -> WorkspaceResult:
        """
        Write every generated file to disk.
        """

        for generated_file in project.files:

            # * -------------------------------------
            # * Skip invalid paths
            # * -------------------------------------

            if not generated_file.path.strip():

                continue

            # * -------------------------------------
            # * Normalize path
            # * -------------------------------------

            normalized_path = generated_file.path.replace("\\", "/")

            # * -------------------------------------
            # * Arduino IDE
            #
            # * Keep the sketch filename exactly as
            # * generated (ProjectName.ino)
            # * -------------------------------------

            if generated_file.extension == ".ino":

                normalized_path = generated_file.name

            # * -------------------------------------
            # * Final path
            # * -------------------------------------

            full_path = (

                Path(result.project_path)

                / Path(normalized_path)

            )

            # * -------------------------------------
            # * Write file
            # * -------------------------------------

            success = self.writer.write(

                str(full_path),

                generated_file.content,

                generated_file.encoding,

            )

            if not success:

                result.errors.append(

                    f"Failed to write file: {generated_file.path}"

                )

            # * -------------------------------------
            # * Record created file
            # * -------------------------------------

            created = CreatedFile(

                name=generated_file.name,

                path=str(full_path),

                extension=generated_file.extension,

                size=len(
                    generated_file.content.encode(
                        generated_file.encoding
                    )
                ),

                encoding=generated_file.encoding,

                created=success,

            )

            result.files.append(created)

        # * -------------------------------------
        # * Statistics
        # * -------------------------------------

        result.file_count = sum(

            1

            for file in result.files

            if file.created

        )

        result.bytes_written = sum(

            file.size

            for file in result.files

            if file.created

        )

        return result