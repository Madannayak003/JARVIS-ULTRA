"""
JARVIS PRO
Developer Editor

Target Locator
"""

import re

from collections import defaultdict

from brain.developer.editor.models.project_index import (
    ProjectIndex,
)


class TargetLocator:
    """
    Locates the most relevant project files for an
    edit request.

    Supports:

        - Filename matching
        - Function matching
        - Class matching
        - Import matching
        - Common project files
        - Web/UI edit detection
        - HTML/CSS/JavaScript targeting

    The goal is to make requests such as:

        "add a blue border around the login card"

    correctly locate existing files such as:

        index.html
        styles.css

    without requiring those words to appear in
    the filenames.
    """

    COMMON_FILES = {

        "readme": "readme",
        "license": "license",
        "requirements": "requirements",
        "main": "main",
        "test": "test",
        "config": "config",
        "settings": "settings",

    }

    MAX_RESULTS = 5

    # * ==================================================
    # * Web / UI vocabulary
    # * ==================================================

    UI_WORDS = {

        "login",
        "signin",
        "sign",
        "signup",
        "register",
        "account",

        "page",
        "card",
        "button",
        "form",
        "input",
        "textarea",
        "select",
        "checkbox",
        "radio",

        "header",
        "footer",
        "navbar",
        "navigation",
        "menu",

        "section",
        "container",
        "panel",
        "modal",
        "popup",
        "dialog",

        "link",
        "image",
        "icon",

        "layout",
        "design",
        "theme",
        "screen",
        "element",

        "border",
        "background",
        "color",
        "font",
        "text",
        "shadow",
        "radius",
        "rounded",

        "padding",
        "margin",
        "spacing",

        "width",
        "height",

        "position",
        "display",
        "flex",
        "grid",

        "responsive",
        "mobile",
        "desktop",

        "animation",
        "transition",

        "hover",
        "focus",

        "dark",
        "light",

    }

    # * ==================================================
    # * Web edit categories
    # * ==================================================

    CSS_TERMS = {

        "border",
        "background",
        "color",
        "font",
        "text",
        "shadow",
        "radius",
        "rounded",

        "padding",
        "margin",
        "spacing",

        "width",
        "height",

        "position",
        "display",
        "flex",
        "grid",

        "responsive",
        "mobile",
        "desktop",

        "animation",
        "transition",

        "hover",
        "focus",

        "style",
        "styles",

        "theme",
        "design",

    }

    HTML_TERMS = {

        "html",
        "page",

        "login",
        "signin",
        "signup",
        "register",

        "form",
        "input",
        "button",
        "textarea",
        "select",
        "checkbox",
        "radio",

        "header",
        "footer",
        "navbar",
        "navigation",
        "menu",

        "section",
        "container",
        "card",

        "link",
        "image",
        "icon",

        "modal",
        "popup",
        "dialog",

        "element",

    }

    JAVASCRIPT_TERMS = {

        "javascript",
        "js",

        "click",
        "onclick",
        "submit",

        "login",
        "signin",
        "signup",
        "register",

        "validate",
        "validation",

        "toggle",
        "open",
        "close",

        "modal",
        "popup",

        "animation",

        "interaction",
        "behavior",
        "behaviour",

    }

    # * ==================================================
    # * Edit verbs to ignore when matching words
    # * ==================================================

    IGNORE_WORDS = {

        "fix",
        "add",
        "remove",
        "replace",
        "rename",
        "update",
        "format",
        "optimize",
        "optimise",
        "refactor",
        "implement",
        "insert",
        "delete",
        "repair",
        "solve",
        "change",
        "modify",
        "edit",
        "write",
        "create",
        "make",
        "build",
        "develop",
        "generate",

    }

    # * ==================================================
    # * Init
    # * ==================================================

    def __init__(self):

        pass

    # * ==================================================
    # * Locate
    # * ==================================================

    def locate(
        self,
        request: str,
        index: ProjectIndex,
    ) -> list[str]:

        if index is None:

            return []

        if not index.files:

            return []

        request = (
            request
            .lower()
            .strip()
        )

        words = {

            word.lower()

            for word in re.findall(

                r"[A-Za-z_][A-Za-z0-9_]*",

                request,

            )

        }

        # * ------------------------------------------
        # * Remove edit verbs
        # * ------------------------------------------

        words -= self.IGNORE_WORDS

        scores = defaultdict(int)

        # * ==================================================
        # * 1. Exact filename
        # * +100
        # * ==================================================

        for file in index.files:

            filename = (
                file
                .replace("\\", "/")
                .split("/")[-1]
                .lower()
            )

            if filename in request:

                scores[file] += 100

        # * ==================================================
        # * 2. Filename stem
        # * +80
        # * ==================================================

        for file in index.files:

            filename = (
                file
                .replace("\\", "/")
                .split("/")[-1]
                .lower()
            )

            if "." in filename:

                stem = filename.rsplit(
                    ".",
                    1,
                )[0]

            else:

                stem = filename

            if stem in words:

                scores[file] += 80

        # * ==================================================
        # * 3. Partial filename
        # * +60
        # * ==================================================

        for file in index.files:

            filename = (
                file
                .replace("\\", "/")
                .split("/")[-1]
                .lower()
            )

            stem = (
                filename.rsplit(
                    ".",
                    1,
                )[0]
                if "." in filename
                else filename
            )

            for word in words:

                if len(word) < 2:

                    continue

                if word in stem:

                    scores[file] += 60

        # * ==================================================
        # * 4. Common project files
        # * +50
        # * ==================================================

        for keyword, value in self.COMMON_FILES.items():

            if keyword not in words:

                continue

            for file in index.files:

                if value in file.lower():

                    scores[file] += 50

        # * ==================================================
        # * 5. Python functions
        # * +90
        # * ==================================================

        for word in words:

            for function_name, files in index.functions.items():

                function_lower = (
                    function_name.lower()
                )

                if word == function_lower:

                    for file in files:

                        scores[file] += 90

                elif word in function_lower:

                    for file in files:

                        scores[file] += 70

        # * ==================================================
        # * 6. Python classes
        # * +85
        # * ==================================================

        for word in words:

            matching_classes = (
                index.classes.get(
                    word,
                    [],
                )
            )

            for file in matching_classes:

                scores[file] += 85

        # * ==================================================
        # * 7. Imports
        # * +40
        # * ==================================================

        for word in words:

            for import_name, files in index.imports.items():

                import_lower = (
                    import_name.lower()
                )

                if (
                    word == import_lower
                    or word in import_lower
                ):

                    for file in files:

                        scores[file] += 40

        # * ==================================================
        # * 8. Detect UI request
        # * ==================================================

        ui_words = (
            words
            & self.UI_WORDS
        )

        if ui_words:

            self._score_web_files(

                words,
                index,
                scores,

            )

        # * ==================================================
        # * 9. Prefer explicit extension requests
        # * ==================================================

        self._score_explicit_extensions(

            request,
            index,
            scores,

        )

        # * ==================================================
        # * 10. Nothing matched
        # * ==================================================

        if not scores:

            return []

        # * ==================================================
        # * 11. Prefer source files
        # * ==================================================

        for file in scores:

            lower = file.lower()

            if lower.endswith(

                (

                    ".py",
                    ".cpp",
                    ".ino",
                    ".c",
                    ".h",
                    ".hpp",

                )

            ):

                scores[file] += 5

        # * ==================================================
        # * 12. Rank
        # * ==================================================

        ranked = sorted(

            scores.items(),

            key=lambda item: (

                -item[1],

                item[0].lower(),

            ),

        )

        return [

            file

            for file, score in ranked[
                : self.MAX_RESULTS
            ]

        ]

    # * ==================================================
    # * Web File Scoring
    # * ==================================================

    def _score_web_files(
        self,
        words: set[str],
        index: ProjectIndex,
        scores,
    ) -> None:
        """
        Score HTML/CSS/JavaScript files based on
        the semantic type of the requested edit.
        """

        css_requested = bool(
            words & self.CSS_TERMS
        )

        html_requested = bool(
            words & self.HTML_TERMS
        )

        javascript_requested = bool(
            words & self.JAVASCRIPT_TERMS
        )

        for file in index.files:

            lower = file.lower()

            # * ------------------------------------------
            # * CSS
            # * ------------------------------------------

            if lower.endswith(".css"):

                if css_requested:

                    scores[file] += 95

                elif html_requested:

                    scores[file] += 35

                else:

                    scores[file] += 20

            # * ------------------------------------------
            # * HTML
            # * ------------------------------------------

            elif lower.endswith(
                (
                    ".html",
                    ".htm",
                )
            ):

                if html_requested:

                    scores[file] += 95

                elif css_requested:

                    scores[file] += 35

                else:

                    scores[file] += 20

            # * ------------------------------------------
            # * JavaScript
            # * ------------------------------------------

            elif lower.endswith(
                (
                    ".js",
                    ".jsx",
                    ".ts",
                    ".tsx",
                )
            ):

                if javascript_requested:

                    scores[file] += 95

                elif html_requested:

                    scores[file] += 25

                else:

                    scores[file] += 15

    # * ==================================================
    # * Explicit Extension Scoring
    # * ==================================================

    def _score_explicit_extensions(
        self,
        request: str,
        index: ProjectIndex,
        scores,
    ) -> None:
        """
        Give very high priority when the user explicitly
        specifies a file type.
        """

        extension_rules = {

            ".html": (
                "html",
                "htm",
            ),

            ".css": (
                "css",
                "stylesheet",
                "styles",
            ),

            ".js": (
                "javascript",
                "js",
            ),

            ".py": (
                "python",
                "py",
            ),

            ".ino": (
                "arduino",
                "esp32",
                "ino",
            ),

        }

        for extension, keywords in extension_rules.items():

            if not any(
                keyword in request
                for keyword in keywords
            ):

                continue

            for file in index.files:

                if file.lower().endswith(
                    extension
                ):

                    scores[file] += 120