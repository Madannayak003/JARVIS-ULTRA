"""
JARVIS PRO
Developer Prompt Builder

Context Builder
"""

from brain.developer.prompt_builder.builders.base_builder import BaseBuilder

from brain.developer.prompt_builder.models.prompt_context import PromptContext


class ContextBuilder(BaseBuilder):
    """
    Builds the project context.
    """

    def build(self, context: PromptContext) -> str:

        analysis = context.analysis

        plan = context.execution_plan

        lines = [

            "# Project Context",

            "",

            f"User Request : {context.user_request}",

            f"Language     : {analysis.language.name}",

            f"Framework    : {analysis.framework.name}",

            f"Project Type : {analysis.project_type.name}",

            f"Workspace    : {analysis.workspace.name}",

            f"Runtime      : {analysis.runtime.name}",

            f"Board        : {analysis.board.name}",

            "",

            "# Project Structure",

            "",

        ]

        # * -------------------------------------
        # * Arduino IDE projects
        # * -------------------------------------

        if analysis.workspace.name == "ARDUINO":

            if plan.files:

                lines.append("Files:")

                for file in plan.files:

                    lines.append(f"- {file}")

                lines.append("")

        # * -------------------------------------
        # * Other workspaces
        # * -------------------------------------

        else:

            if plan.folders:

                lines.append("Folders:")

                for folder in plan.folders:

                    lines.append(f"- {folder}")

                lines.append("")

            if plan.files:

                lines.append("Files:")

                for file in plan.files:

                    lines.append(f"- {file}")

                lines.append("")

        # * -------------------------------------
        # * Dependencies
        # * -------------------------------------

        if plan.dependencies:

            lines.append("Dependencies:")

            for dependency in plan.dependencies:

                lines.append(f"- {dependency}")

            lines.append("")

        return "\n".join(lines)