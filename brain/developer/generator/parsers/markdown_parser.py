"""
JARVIS PRO
Developer Generator

Markdown Parser
"""

import re

from brain.developer.generator.models.generated_file import GeneratedFile
from brain.developer.generator.models.generated_project import GeneratedProject


class MarkdownParser:
    """
    Parses Markdown returned by an LLM into a GeneratedProject.

    Supported formats:

        # * FILE: src/main.py
        ```python
        ...
        ```

        # * FILE: requirements.txt
        pytest

        # * FILE: .gitignore
        ```

    Supports nested paths and both Windows/Linux path separators.
    """

    # * ---------------------------------------------------------
    # * FILE header
    # * ---------------------------------------------------------

    FILE_HEADER_PATTERN = re.compile(
        r"^\s*#\s*FILE:\s*(.+?)\s*$",
        re.MULTILINE | re.IGNORECASE,
    )

    # * ---------------------------------------------------------
    # * Code fence
    # * ---------------------------------------------------------

    CODE_FENCE_PATTERN = re.compile(
        r"^```([\w.+#-]*)\s*\n(.*?)^```\s*$",
        re.MULTILINE | re.DOTALL,
    )

    # * ---------------------------------------------------------
    # * Parse
    # * ---------------------------------------------------------

    def parse(
        self,
        response: str,
    ) -> GeneratedProject:
        """
        Parse Markdown into a GeneratedProject.
        """

        project = GeneratedProject()

        if not response or not response.strip():

            project.generated = False

            project.errors.append(
                "Empty response received from AI."
            )

            return project

        # * ---------------------------------------------
        # * Find every FILE header
        # * ---------------------------------------------

        headers = list(
            self.FILE_HEADER_PATTERN.finditer(
                response
            )
        )

        if not headers:

            project.generated = False

            project.errors.append(
                "No project files found in AI response."
            )

            return project

        # * ---------------------------------------------
        # * Parse each FILE section
        # * ---------------------------------------------

        for index, header in enumerate(headers):

            path = header.group(1).strip()

            path = (
                path
                .replace("\\", "/")
                .strip()
            )

            if not path:
                continue

            # * -----------------------------------------
            # * Section boundaries
            # * -----------------------------------------

            content_start = header.end()

            if index + 1 < len(headers):

                content_end = headers[
                    index + 1
                ].start()

            else:

                content_end = len(response)

            section = response[
                content_start:content_end
            ]

            section = section.lstrip(
                "\r\n"
            )

            # * -----------------------------------------
            # * Parse fenced content
            # * -----------------------------------------

            fence_match = (
                self.CODE_FENCE_PATTERN.search(
                    section
                )
            )

            if fence_match:

                markdown_language = (
                    fence_match.group(1).strip()
                )

                content = fence_match.group(2)

            else:

                # * -------------------------------------
                # * Plain text file
                # * -------------------------------------

                markdown_language = ""

                content = section

                # * Remove accidental separator lines
                # * before the next FILE block.
                content = content.rstrip(
                    "\r\n"
                )

            # * -----------------------------------------
            # * Remove trailing markdown separators
            # * -----------------------------------------

            content = self._clean_content(
                content
            )

            generated_file = GeneratedFile(

                name=self._get_name(path),

                path=path,

                extension=self._get_extension(path),

                content=content,

                language=self._get_language(path),

                markdown_language=markdown_language,

                size=len(
                    content.encode(
                        "utf-8"
                    )
                ),

                line_count=len(
                    content.splitlines()
                ),

                is_empty=(
                    len(
                        content.strip()
                    ) == 0
                ),

            )

            project.files.append(
                generated_file
            )

        # * ---------------------------------------------
        # * Project status
        # * ---------------------------------------------

        project.generated = (
            len(project.files) > 0
        )

        project.file_count = (
            len(project.files)
        )

        project.total_characters = sum(
            file.size
            for file in project.files
        )

        return project

    # * ---------------------------------------------------------
    # * Clean content
    # * ---------------------------------------------------------

    @staticmethod
    def _clean_content(
        content: str,
    ) -> str:
        """
        Clean common formatting artifacts
        without changing actual file content.
        """

        content = content.rstrip(
            "\r\n"
        )

        # * Remove a markdown separator accidentally
        # * returned after the file.
        if content.endswith(
            "\n================================================================================"
        ):

            content = content[
                :-len(
                    "\n================================================================================"
                )
            ]

            content = content.rstrip(
                "\r\n"
            )

        return content

    # * ---------------------------------------------------------
    # * File name
    # * ---------------------------------------------------------

    @staticmethod
    def _get_name(
        path: str,
    ) -> str:

        return (
            path
            .replace("\\", "/")
            .split("/")[-1]
        )

    # * ---------------------------------------------------------
    # * Extension
    # * ---------------------------------------------------------

    @staticmethod
    def _get_extension(
        path: str,
    ) -> str:

        name = (
            path
            .replace("\\", "/")
            .split("/")[-1]
        )

        if "." not in name:

            return ""

        return (
            "."
            + name.split(".")[-1].lower()
        )

    # * ---------------------------------------------------------
    # * Language
    # * ---------------------------------------------------------

    @staticmethod
    def _get_language(
        path: str,
    ) -> str:

        extension = (
            MarkdownParser
            ._get_extension(path)
        )

        languages = {

            ".py": "Python",

            ".cpp": "C++",
            ".c": "C",
            ".h": "C++",
            ".hpp": "C++",

            ".ino": "Arduino",

            ".java": "Java",
            ".kt": "Kotlin",
            ".cs": "C#",

            ".go": "Go",
            ".rs": "Rust",
            ".php": "PHP",

            ".sh": "Shell",
            ".bat": "Batch",
            ".ps1": "PowerShell",

            ".sql": "SQL",
            ".dart": "Dart",
            ".swift": "Swift",

            ".vue": "Vue",
            ".jsx": "React",
            ".tsx": "React",

            ".html": "HTML",
            ".css": "CSS",

            ".js": "JavaScript",
            ".ts": "TypeScript",

            ".json": "JSON",
            ".md": "Markdown",

            ".txt": "Text",

            ".xml": "XML",

            ".yml": "YAML",
            ".yaml": "YAML",

            ".ini": "INI",

        }

        return languages.get(
            extension,
            "",
        )