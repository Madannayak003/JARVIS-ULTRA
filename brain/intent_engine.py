"""
JARVIS PRO
Stage 5

Intent Engine

Central routing engine for deciding
how a user request should be processed.
"""

from __future__ import annotations

from dataclasses import dataclass


# * ==========================================================
# * Result
# * ==========================================================

@dataclass
class IntentResult:

    mode: str

    confidence: float

    reason: str


# * ==========================================================
# * Engine
# * ==========================================================

class IntentEngine:

    # * ------------------------------------------------------
    # * Developer action words
    # * ------------------------------------------------------

    DEVELOPER_ACTIONS = {

        "create",
        "build",
        "make",
        "develop",
        "implement",

        "add",
        "remove",
        "delete",

        "update",
        "modify",
        "change",

        "fix",
        "repair",

        "refactor",
        "optimize",

        "rename",

        "replace",

        "edit",

        "write",
        "generate",

    }

    # * ------------------------------------------------------
    # * Developer technologies / code terms
    # * ------------------------------------------------------

    DEVELOPER_TECHNOLOGIES = {

        "python",
        "java",
        "javascript",
        "typescript",

        "html",
        "css",

        "react",
        "vue",
        "angular",

        "cpp",
        "c++",
        "c",

        "arduino",
        "esp32",
        "esp8266",

        "sql",

        "firebase",
        "mqtt",

        "api",

    }

    # * ------------------------------------------------------
    # * Developer objects
    # * ------------------------------------------------------

    DEVELOPER_OBJECTS = {

        "code",
        "function",
        "class",

        "script",
        "program",

        "calculator",
        "website",
        "webapp",
        "application",
        "app",

        "project",

        "file",
        "files",

        "module",

        "bug",
        "error",

        "feature",

    }

    # * ------------------------------------------------------
    # * Developer file extensions
    # * ------------------------------------------------------

    DEVELOPER_EXTENSIONS = {

        ".py",
        ".js",
        ".ts",
        ".html",
        ".css",

        ".cpp",
        ".c",
        ".h",
        ".hpp",

        ".ino",

        ".json",
        ".xml",
        ".yaml",
        ".yml",

    }

    # * ------------------------------------------------------
    # * Chat prefixes
    # * ------------------------------------------------------

    CHAT_PREFIXES = {

        "what",
        "who",
        "where",
        "when",
        "why",
        "how",

        "tell",
        "describe",
        "define",
        "explain",

        "compare",
        "difference",

        "continue",

        "summarize",

        "can you",
        "could you",
        "would you",

        "do you know",

    }

    # * ------------------------------------------------------
    # * Chat keywords
    # * ------------------------------------------------------

    CHAT_KEYWORDS = {

        # * Learning

        "tutorial",
        "guide",
        "learn",

        # * Conversation

        "joke",
        "story",
        "poem",

        # * Explanation

        "meaning",
        "definition",

        # * Follow-up

        "thanks",
        "thank",
        "thank you",

    }

    # * ------------------------------------------------------
    # * Planner / system actions
    # * ------------------------------------------------------

    ACTION_PREFIXES = {

        "open",
        "launch",
        "close",

        "shutdown",
        "restart",

        "search",

        "play",

        "stop",

        "delete",

        "copy",
        "move",
        "rename",
        "send",
        "call",

        "turn on",
        "turn off",

        "increase",
        "decrease",

    }

    # * ======================================================
    # * Constructor
    # * ======================================================

    def __init__(
        self,
        state=None,
    ):

        self.state = state

    # * ======================================================
    # * Detect
    # * ======================================================

    def detect(
        self,
        command: str,
    ) -> IntentResult:

        command = command.lower().strip()

        if not command:

            return IntentResult(
                mode="chat",
                confidence=1.0,
                reason="empty_command",
            )

        # * ==================================================
        # * Conversation State
        # * ==================================================

        if self.state:

            try:

                if self.state.is_waiting():

                    owner = self.state.owner()

                    return IntentResult(
                        mode=owner,
                        confidence=1.0,
                        reason="conversation_state",
                    )

            except Exception:

                pass

        # * ==================================================
        # * Planner
        # * ==================================================

        for prefix in self.ACTION_PREFIXES:

            if command.startswith(prefix):

                return IntentResult(
                    mode="planner",
                    confidence=0.98,
                    reason=f"action_prefix:{prefix}",
                )
                
        # * ==================================================
        # * Personal Notes
        #
        # ! Notes are normal assistant commands and must
        # * always be handled before Developer Detection.
        # * ==================================================

        NOTE_PREFIXES = (
            "make a note",
            "make note",
            "take a note",
            "take note",
            "create a note",
            "create note",
            "save a note",
            "save note",
            "write a note",
            "write note",
            "add a note",
            "add note",
        )

        if command.startswith(NOTE_PREFIXES):

            return IntentResult(
                mode="planner",
                confidence=0.99,
                reason="personal_note_command",
            )                
                

        # * ==================================================
        # * Developer Detection
        #
        # ! IMPORTANT:
        #
        # * We check developer requests BEFORE chat
        # * keywords.
        #
        # * This prevents:
        #
        # * create python calculator
        #
        # * from becoming chat because of "python".
        # * ==================================================

        words = set(
            command.replace(
                ",",
                " ",
            ).split()
        )

        developer_action = None

        for action in self.DEVELOPER_ACTIONS:

            if action in words:

                developer_action = action

                break

        technology_found = any(

            technology in command

            for technology
            in self.DEVELOPER_TECHNOLOGIES

        )

        object_found = any(

            obj in words

            for obj
            in self.DEVELOPER_OBJECTS

        )

        extension_found = any(

            extension in command

            for extension
            in self.DEVELOPER_EXTENSIONS

        )

        # * --------------------------------------------------
        # * Strong developer request
        #
        # * Example:
        #
        # * create python calculator
        # * build html website
        # * add function
        # * fix divide function
        # * --------------------------------------------------

        if (

            developer_action
            and (
                technology_found
                or object_found
                or extension_found
            )

        ):

            return IntentResult(

                mode="developer",

                confidence=0.99,

                reason=(
                    "developer_action:"
                    f"{developer_action}"
                ),

            )

        # * --------------------------------------------------
        # * Strong coding request
        #
        # * Example:
        #
        # * write python code
        # * generate javascript
        # * create html
        # * --------------------------------------------------

        if (

            developer_action
            and technology_found

        ):

            return IntentResult(

                mode="developer",

                confidence=0.98,

                reason=(
                    "developer_technology:"
                    f"{developer_action}"
                ),

            )

        # * ==================================================
        # * Chat Prefix
        # * ==================================================

        for prefix in self.CHAT_PREFIXES:

            if command.startswith(prefix):

                return IntentResult(

                    mode="chat",

                    confidence=0.97,

                    reason=f"chat_prefix:{prefix}",

                )

        # * ==================================================
        # * Chat Keyword
        # * ==================================================

        for keyword in self.CHAT_KEYWORDS:

            if keyword in command:

                return IntentResult(

                    mode="chat",

                    confidence=0.95,

                    reason=f"chat_keyword:{keyword}",

                )

        # * ==================================================
        # * Default
        # * ==================================================

        return IntentResult(

            mode="planner",

            confidence=0.50,

            reason="default",

        )