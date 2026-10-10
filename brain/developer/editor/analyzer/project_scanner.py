"""
JARVIS PRO
Developer Editor

Project Scanner
"""

import ast
from pathlib import Path

from brain.developer.editor.models.project_index import (
    ProjectIndex,
)


class ProjectScanner:
    """
    Scans a project and builds a ProjectIndex.

    Supports:
        Python
        Arduino
        C / C++
        HTML
        CSS
        JavaScript
        TypeScript
        JSON
        XML
        YAML
        TOML
    """

    SUPPORTED_EXTENSIONS = {

        # * Python
        ".py",

        # * Arduino / C / C++
        ".ino",
        ".cpp",
        ".c",
        ".h",
        ".hpp",

        # * Web
        ".html",
        ".htm",
        ".css",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",

        # * Data / configuration
        ".json",
        ".xml",
        ".yaml",
        ".yml",
        ".toml",
    }

    # ! Directories that should never become Developer targets.
    IGNORED_DIRECTORIES = {

        ".git",
        ".svn",
        ".hg",

        "__pycache__",

        "node_modules",

        ".venv",
        "venv",

        "env",

        "dist",
        "build",

        ".next",

        "coverage",

        ".pytest_cache",

        ".mypy_cache",

        ".idea",
        ".vscode",
    }

    # * --------------------------------------------------
    # * Scan
    # * --------------------------------------------------

    def scan(
        self,
        project_path: str,
    ) -> ProjectIndex:

        index = ProjectIndex()

        root = Path(
            project_path,
        )

        if not root.exists():

            return index

        if not root.is_dir():

            return index

        # * ----------------------------------------------
        # * Walk project
        # * ----------------------------------------------

        for file in root.rglob("*"):

            if not file.is_file():

                continue

            # * ------------------------------------------
            # * Ignore generated / dependency directories
            # * ------------------------------------------

            if any(

                part in self.IGNORED_DIRECTORIES

                for part in file.parts

            ):

                continue

            # * ------------------------------------------
            # * Extension
            # * ------------------------------------------

            extension = file.suffix.lower()

            if extension not in self.SUPPORTED_EXTENSIONS:

                continue

            # * ------------------------------------------
            # * Relative path
            # * ------------------------------------------

            relative = str(

                file.relative_to(root)

            ).replace("\\", "/")

            index.files.append(

                relative,

            )

            # * ------------------------------------------
            # * Python analysis
            # * ------------------------------------------

            if extension == ".py":

                self._scan_python(

                    file,

                    relative,

                    index,

                )

        # * ----------------------------------------------
        # * Stable ordering
        # * ----------------------------------------------

        index.files = sorted(

            set(index.files),

        )

        return index

    # * --------------------------------------------------
    # * Python Scanner
    # * --------------------------------------------------

    def _scan_python(
        self,
        file: Path,
        relative: str,
        index: ProjectIndex,
    ):

        try:

            source = file.read_text(
                encoding="utf-8",
            )

        except UnicodeDecodeError:

            try:

                source = file.read_text(
                    encoding="utf-8-sig",
                )

            except Exception:

                return

        except Exception:

            return

        try:

            tree = ast.parse(
                source,
            )

        except Exception:

            return

        for node in ast.walk(tree):

            # * ------------------------------------------
            # * Functions
            # * ------------------------------------------

            if isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            ):

                index.functions.setdefault(

                    node.name,

                    [],

                ).append(

                    relative,

                )

            # * ------------------------------------------
            # * Classes
            # * ------------------------------------------

            elif isinstance(
                node,
                ast.ClassDef,
            ):

                index.classes.setdefault(

                    node.name,

                    [],

                ).append(

                    relative,

                )

            # * ------------------------------------------
            # * import x
            # * ------------------------------------------

            elif isinstance(
                node,
                ast.Import,
            ):

                for alias in node.names:

                    index.imports.setdefault(

                        alias.name,

                        [],

                    ).append(

                        relative,

                    )

            # * ------------------------------------------
            # * from x import y
            # * ------------------------------------------

            elif isinstance(
                node,
                ast.ImportFrom,
            ):

                module = node.module or ""

                if module:

                    index.imports.setdefault(

                        module,

                        [],

                    ).append(

                        relative,

                    )