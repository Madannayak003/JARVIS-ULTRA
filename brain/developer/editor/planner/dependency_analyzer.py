"""
JARVIS PRO
Developer Editor

Dependency Analyzer
"""

from brain.developer.editor.models import (
    EditRequest,
)


class DependencyAnalyzer:
    """
    Expands the selected files by discovering
    related project files.
    """

    # * --------------------------------------------------

    def analyze(
        self,
        request: EditRequest,
    ) -> EditRequest:

        if request.project_index is None:

            return request

        # * ------------------------------------------
        # * Save primary files
        # * ------------------------------------------

        request.primary_files = list(

            request.target_files

        )

        selected = set(

            request.primary_files

        )

        # * ------------------------------------------
        # * Add files that import the selected modules
        # * ------------------------------------------

        for module, files in request.project_index.imports.items():

            for file in files:

                if file in selected:

                    selected.update(files)

        # * ------------------------------------------
        # * Automatically include related tests
        # * ------------------------------------------

        for file in request.project_index.files:

            lower = file.lower()

            if "test" not in lower:

                continue

            for target in request.primary_files:

                stem = target.split("/")[-1]

                stem = stem.rsplit(".", 1)[0].lower()

                if stem in lower:

                    selected.add(file)

        # * ------------------------------------------
        # * Save dependent files
        # * ------------------------------------------

        request.dependent_files = sorted(

            selected - set(request.primary_files)

        )

        request.target_files = sorted(

            selected

        )

        return request