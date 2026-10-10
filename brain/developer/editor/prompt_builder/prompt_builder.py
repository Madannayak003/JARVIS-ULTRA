"""
JARVIS PRO
Developer Editor

Prompt Builder
"""

from brain.developer.editor.models.edit_plan import (
    EditPlan,
)

from brain.developer.editor.models.prompt_context import (
    PromptContext,
)

from brain.developer.editor.models.prompt_result import (
    PromptResult,
)

from brain.developer.editor.prompt_builder.system_builder import (
    SystemBuilder,
)

from brain.developer.editor.prompt_builder.context_builder import (
    ContextBuilder,
)

from brain.developer.editor.prompt_builder.instruction_builder import (
    InstructionBuilder,
)

from brain.developer.editor.workspace.file_reader import (
    FileReader,
)

from brain.developer.editor.workspace.code_extractor import (
    CodeExtractor,
)


class PromptBuilder:

    def __init__(self):

        self.system_builder = SystemBuilder()

        self.context_builder = ContextBuilder()

        self.instruction_builder = InstructionBuilder()
        
        self.reader = FileReader()
        
        self.extractor = CodeExtractor()

    # * --------------------------------------------------

    def build(
        self,
        plan: EditPlan,
    ) -> PromptResult:
        
        request = plan.request

        if request is None:

            raise ValueError(

                "EditPlan has no EditRequest."

            )

        # * --------------------------------------
        # * Read Selected Files
        # * --------------------------------------

        if (

            request.project_path

            and

            request.target_files

        ):

            request.file_contents = self.reader.read(

                request.project_path,

                request.target_files,

            )

            # * request.file_contents = self.extractor.extract(

            # * request.user_request,

            # * request.edit_type,

            # * request.file_contents,

            # * )

        # * --------------------------------------

        context = PromptContext(

            request=request,

        )

        system = self.system_builder.build(

            context,

        )

        user = (

            self.context_builder.build(

                context,

            )

            + "\n\n"

            + self.instruction_builder.build()

        )

        return PromptResult(

            system_prompt=system,

            user_prompt=user,

            prompt=system + "\n\n" + user,

        )