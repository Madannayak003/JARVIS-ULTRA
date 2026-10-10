"""
JARVIS PRO
Developer Analyzer

Analyzer Engine
"""

from brain.developer.models.analysis_context import AnalysisContext
from brain.developer.models.analysis_result import AnalysisResult

from brain.developer.analyzer.detectors.intent_detector import IntentDetector
from brain.developer.analyzer.detectors.language_detector import LanguageDetector
from brain.developer.analyzer.detectors.framework_detector import FrameworkDetector
from brain.developer.analyzer.detectors.workspace_detector import WorkspaceDetector
from brain.developer.analyzer.detectors.project_detector import ProjectDetector
from brain.developer.analyzer.detectors.runtime_detector import RuntimeDetector
from brain.developer.analyzer.detectors.board_detector import BoardDetector
from brain.developer.analyzer.resolvers.language_resolver import LanguageResolver
from brain.developer.analyzer.resolvers.board_resolver import BoardResolver
from brain.developer.analyzer.resolvers.workspace_resolver import WorkspaceResolver


class Analyzer:
    """
    Main analyzer engine.
    """

    def __init__(self):

        self.intent_detector = IntentDetector()

        self.language_detector = LanguageDetector()

        self.framework_detector = FrameworkDetector()

        self.workspace_detector = WorkspaceDetector()

        self.project_detector = ProjectDetector()

        self.runtime_detector = RuntimeDetector()

        self.board_detector = BoardDetector()
        
        self.resolvers = [

            LanguageResolver(),

            BoardResolver(),

            WorkspaceResolver(),

        ]
        

    def create_context(self, text: str) -> AnalysisContext:

        return self.intent_detector.create_context(text)

    def analyze(self, text: str) -> AnalysisResult:

        context = self.create_context(text)

        result = AnalysisResult(

            user_request=text,

            intent=self.intent_detector.detect(context),

            language=self.language_detector.detect(context),

            framework=self.framework_detector.detect(context),

            workspace=self.workspace_detector.detect(context),

            project_type=self.project_detector.detect(context),

            runtime=self.runtime_detector.detect(context),

            board=self.board_detector.detect(context),

        )

        # * Resolve inferred values

        for resolver in self.resolvers:
            resolver.resolve(result)

        return result