"""
JARVIS PRO
Developer Generator

Response Parser
"""

from brain.developer.generator.models.generated_project import GeneratedProject

from brain.developer.generator.parsers.markdown_parser import MarkdownParser


class ResponseParser:
    """
    Main response parser.

    Converts raw LLM output into a GeneratedProject.
    Selects the appropriate parser based on the response.
    """

    def __init__(self):

        self.markdown_parser = MarkdownParser()

    # * -----------------------------------------------------

    def parse(
        self,
        response: str,
    ) -> GeneratedProject:
        """
        Parse an LLM response.
        """

        # * ---------------------------------------
        # * Empty Response
        # * ---------------------------------------

        if not response or not response.strip():

            project = GeneratedProject()

            project.generated = False

            project.errors.append(

                "Empty response received from AI."

            )

            return project

        # * ---------------------------------------
        # * Markdown Parser
        # * ---------------------------------------

        project = self.markdown_parser.parse(

            response

        )

        # * ---------------------------------------
        # * Future Parser Selection
        # * ---------------------------------------
        #
        # * Future versions can automatically
        # * choose between:
        #
        # * MarkdownParser
        # * JSONParser
        # * XMLParser
        # * ArchiveParser
        #
        # * ---------------------------------------

        return project