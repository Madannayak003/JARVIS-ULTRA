"""
JARVIS PRO
Developer Editor

Main Editor Engine
"""

from brain.developer.editor.analyzer import (
    EditAnalyzer,
)

from brain.developer.editor.planner import (
    EditPlanner,
)

from brain.developer.editor.prompt_builder import (
    PromptBuilder,
)

from brain.developer.editor.provider.ollama_provider import (
    OllamaProvider,
)

from brain.developer.editor.parser import (
    ResponseParser,
)

from brain.developer.editor.validator.edit_validator import (
    EditValidator,
)

from brain.developer.editor.workspace.patch_writer import (
    PatchWriter,
)

from brain.developer.editor.workspace.file_reader import (
    FileReader,
)


class Editor:
    """
    Main Developer Editor engine.

    Workflow:

        Analyze
            ↓
        Plan
            ↓
        Read complete originals
            ↓
        Build Prompt
            ↓
        Generate
            ↓
        Parse
            ↓
        Validate against originals
            ↓
        Write
    """

    def __init__(self):

        self.analyzer = EditAnalyzer()

        self.planner = EditPlanner()

        self.prompt_builder = PromptBuilder()

        self.provider = OllamaProvider()

        self.parser = ResponseParser()

        self.validator = EditValidator()

        self.writer = PatchWriter()

        self.reader = FileReader()

    # * --------------------------------------------------
    # * Execute
    # * --------------------------------------------------

    def execute(

        self,

        user_request: str,

        project_path: str,

    ):

        # * ------------------------------------------
        # * Analyze
        # * ------------------------------------------

        request = self.analyzer.analyze(

            user_request,

            project_path,

        )

        # * ------------------------------------------
        # * Plan
        # * ------------------------------------------

        plan = self.planner.plan(

            request,

        )

        # * ------------------------------------------
        # * Read COMPLETE original files
        #
        # ! IMPORTANT:
        # * Do this AFTER planning because the planner
        # * may change/expand target_files.
        # * ------------------------------------------

        original_files = self.reader.read(

            project_path,

            plan.target_files,

        )

        print(
            "[EDITOR] Original files captured:",
            list(original_files.keys()),
        )

        # * ------------------------------------------
        # * Build Prompt
        # * ------------------------------------------

        prompt = self.prompt_builder.build(

            plan,

        )

        # * ------------------------------------------
        # * Generate
        # * ------------------------------------------

        response = self.provider.generate(

            prompt,

        )

        # * ------------------------------------------
        # * Generation failed
        # * ------------------------------------------

        if not response:

            print(
                "[EDITOR] AI generation returned no response."
            )

            return None

        # * ------------------------------------------
        # * Parse
        # * ------------------------------------------

        result = self.parser.parse(

            response,

        )

        # * ------------------------------------------
        # * Validate
        #
        # * Compare generated files against the
        # * complete originals.
        # * ------------------------------------------

        result = self.validator.validate(

            result,

            original_files,

        )

        # * ------------------------------------------
        # * Validation failed
        # * ------------------------------------------

        if not result.success:

            print(
                "[EDITOR] Validation failed."
            )

            for error in result.errors:

                print(
                    "[EDITOR VALIDATION ERROR]",
                    error,
                )

            return result

        # * ------------------------------------------
        # * Write
        # * ------------------------------------------

        self.writer.write(

            project_path,

            result.patches,

        )

        print(
            "[EDITOR] Edit written successfully."
        )

        return result