"""
JARVIS PRO
Stage 5

Goal Analyzer

Converts a user request into a structured goal
that the Planner and AI can understand.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Goal:

    category: str

    action: str

    target: str

    objective: str

    confidence: float = 0.50


class GoalAnalyzer:

    def __init__(self):

        pass

    # * --------------------------------------------------

    def analyze(self, command: str) -> Goal:

        text = command.lower().strip()

        # * ------------------------------------------
        # * Coding
        # * ------------------------------------------

        if any(word in text for word in [

            "python",
            "java",
            "javascript",
            "html",
            "css",
            "code",
            "program",
            "script"

        ]):

            return Goal(

                category="coding",

                action="generate",

                target="source_code",

                objective=text,

                confidence=0.95

            )

        # * ------------------------------------------
        # * Browser
        # * ------------------------------------------

        if any(word in text for word in [

            "google",
            "youtube",
            "browser",
            "website"

        ]):

            return Goal(

                category="browser",

                action="search",

                target="web",

                objective=text,

                confidence=0.95

            )

        # * ------------------------------------------
        # * System
        # * ------------------------------------------

        if any(word in text for word in [

            "open",

            "close",

            "shutdown",

            "restart"

        ]):

            return Goal(

                category="system",

                action="execute",

                target="desktop",

                objective=text,

                confidence=0.90

            )

        # * ------------------------------------------
        # * Conversation
        # * ------------------------------------------

        return Goal(

            category="conversation",

            action="respond",

            target="chat",

            objective=text,

            confidence=0.60

        )