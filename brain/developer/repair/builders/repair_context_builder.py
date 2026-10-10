"""
JARVIS PRO
Developer Repair

Repair Context Builder
"""

from .base_builder import BaseBuilder


class RepairContextBuilder(BaseBuilder):

    def build(self, request):

        lines = [

            "# Repair Request",

            "",

        ]

        if request.missing_files:

            lines.append("Missing Files:")

            for file in request.missing_files:

                lines.append(f"- {file}")

            lines.append("")

        if request.missing_folders:

            lines.append("Missing Folders:")

            for folder in request.missing_folders:

                lines.append(f"- {folder}")

            lines.append("")

        return "\n".join(lines)