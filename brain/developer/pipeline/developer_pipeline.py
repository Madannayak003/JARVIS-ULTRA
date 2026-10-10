"""
JARVIS PRO
Developer Pipeline
"""

from brain.developer.context import DeveloperContext

from brain.developer.analyzer import Analyzer
from brain.developer.planner import Planner
from brain.developer.prompt_builder import PromptBuilder
from brain.developer.generator import Generator
from brain.developer.validator import Validator
from brain.developer.workspace import Workspace
from brain.developer.repair import Repair

class DeveloperPipeline:
    """
    Main Developer Pipeline.

    Executes the complete developer workflow.
    """

    def __init__(self):

        self.analyzer = Analyzer()

        self.planner = Planner()

        self.prompt_builder = PromptBuilder()

        self.generator = Generator()
        
        self.validator = Validator()
        
        self.repair = Repair()
        
        self.workspace = Workspace()

    # * ---------------------------------------------------------

    def process(self, user_request: str) -> DeveloperContext:
        """
        Execute the Developer pipeline.
        """

        context = DeveloperContext(

            user_request=user_request,

        )

        # * ----------------------------------------
        # * Analyzer
        # * ----------------------------------------

        print("STEP 1 : Analyzer")

        context.analysis = self.analyzer.analyze(

            context.user_request

        )

        print("Analyzer Done")

        # * ----------------------------------------
        # * Planner
        # * ----------------------------------------

        print("STEP 2 : Planner")

        context.execution_plan = self.planner.create_plan(

            context.analysis

        )

        print("Planner Done")

        # * ----------------------------------------
        # * Prompt Builder
        # * ----------------------------------------

        print("STEP 3 : Prompt Builder")

        context.prompt_result = self.prompt_builder.build(
            context
        )

        print("Prompt Builder Done")
        
        # * ----------------------------------------
        # * Generator
        # * ----------------------------------------

        print("STEP 4 : Generator")

        context.generated_project = self.generator.generate(
            context
        )

        if not context.generated_project.generated:

            print("Generator Failed")

        else:

            print("Generator Done")
        
        # * ----------------------------------------
        # * Validator
        # * ----------------------------------------

        print("STEP 5 : Validator")

        context.validation_result = self.validator.validate(
            context
        )

        print("Validator Done")

        # * ----------------------------------------
        # * Repair (if needed)
        # * ----------------------------------------

        if not context.validation_result.valid:

            print("STEP 6 : Repair")

            context.repair_result = self.repair.repair(
                context
            )

            print("Repair Done")

            # * ------------------------------------
            # * Validate Again
            # * ------------------------------------

            print("STEP 7 : Re-Validator")

            context.validation_result = self.validator.validate(
                context
            )

            print("Re-Validator Done")

        # * ----------------------------------------
        # * Workspace
        # * ----------------------------------------

        if context.validation_result.valid:

            print("STEP 8 : Workspace")

            context.workspace_result = self.workspace.create(
                context
            )

            print("Workspace Done")

        else:

            print("Workspace Skipped (Validation Failed)")

        return context