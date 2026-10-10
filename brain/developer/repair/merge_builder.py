"""
JARVIS PRO
Developer Repair

Merge Builder
"""

from brain.developer.generator.models.generated_project import (
    GeneratedProject,
)


class MergeBuilder:
    """
    Merges repaired files into
    the original generated project.
    """

    def build(
        self,
        project: GeneratedProject,
        repaired_project: GeneratedProject,
    ) -> GeneratedProject:

        existing = {

            file.path: file

            for file in project.files

        }

        # * -----------------------------
        # * Replace / Add repaired files
        # * -----------------------------

        for file in repaired_project.files:

            existing[file.path] = file

        # * -----------------------------
        # * Update project
        # * -----------------------------

        project.files = list(existing.values())

        project.file_count = len(project.files)

        project.generated = len(project.files) > 0

        return project