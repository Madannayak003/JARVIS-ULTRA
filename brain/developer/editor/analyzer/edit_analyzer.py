"""
JARVIS PRO
Developer Editor

Edit Analyzer
"""

import re

from brain.developer.editor.models import (
    EditRequest,
)

from brain.developer.editor.analyzer.target_locator import (
    TargetLocator,
)

from brain.developer.editor.analyzer.project_scanner import (
    ProjectScanner,
)

class EditAnalyzer:
    """
    Analyzes a user's editing request and
    converts it into an EditRequest.
    """

    ACTION_RULES = {

        # * -------------------------------------
        # * Highest priority
        # * -------------------------------------

        "RENAME": [

            r"\brename\b",

        ],

        "REPLACE": [

            r"\breplace\b",
            r"\bswap\b",

        ],

        "REMOVE": [

            r"\bremove\b",
            r"\bdelete\b",

        ],

        "FIX": [

            r"\bfix\b",
            r"\brepair\b",
            r"\bsolve\b",

        ],

        "UPDATE": [

            r"\bupdate\b",
            r"\bupgrade\b",

        ],

        "REFACTOR": [

            r"\brefactor\b",

        ],

        "OPTIMIZE": [

            r"\boptimi[sz]e\b",

        ],

        "FORMAT": [

            r"\bformat\b",

        ],

        # * -------------------------------------
        # * Lowest priority
        # * -------------------------------------

        "ADD": [

            r"\badd\b",
            r"\binsert\b",
            r"\binclude\b",
            r"\bimplement\b",

        ],

    }

    DEFAULT_ACTION = "MODIFY"

    # * --------------------------------------------------

    def __init__(self):

        self.target_locator = TargetLocator()
        self.scanner = ProjectScanner()

    # * --------------------------------------------------

    def analyze(
        self,
        user_request: str,
        project_path: str = "",
    ) -> EditRequest:
        """
        Analyze the edit request.
        """

        request = EditRequest()

        request.user_request = user_request.strip()

        request.edit_type = self._detect_action(

            request.user_request,

        )

        request.instructions.append(

            request.user_request,

        )

        if project_path:

            request.project_path = project_path

            # * ---------------------------------
            # * Build project index
            # * ---------------------------------

            request.project_index = self.scanner.scan(

                project_path,

            )

            # * ---------------------------------
            # * Locate relevant files
            # * ---------------------------------

            request.target_files = self.target_locator.locate(

                request.user_request,

                request.project_index,

            )

        return request

    # * --------------------------------------------------

    def _detect_action(
        self,
        user_request: str,
    ) -> str:
        """
        Detect the requested edit action.
        """

        request = user_request.lower().strip()

        # * -------------------------------------
        # * Priority-based detection
        # * -------------------------------------

        for action, patterns in self.ACTION_RULES.items():

            for pattern in patterns:

                if re.search(

                    pattern,

                    request,

                    re.IGNORECASE,

                ):

                    return action

        return self.DEFAULT_ACTION