"""
JARVIS PRO
Developer Memory

Memory Context
"""

from typing import Any


class MemoryContext:
    """
    Builds a compact context from Developer Memory.
    """

    def __init__(
        self,
        search=None,
    ):
        self.search = search

    # * --------------------------------------------------
    # * Configure
    # * --------------------------------------------------

    def set_search(
        self,
        search,
    ) -> None:
        """
        Set the memory search engine.
        """

        self.search = search

    # * --------------------------------------------------
    # * Build
    # * --------------------------------------------------

    def build(
        self,
        query: str = "",
        memory: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Build relevant memory context.

        If a search engine is available and a query
        is supplied, matching memories are included.
        """

        context = {

            "project": {},
            "files": {},
            "symbols": {},
            "dependencies": [],
            "style": {},
            "edits": [],
            "session": {},

            "matches": [],

        }

        if not memory:
            return context

        # * ------------------------------------------
        # * Basic project context
        # * ------------------------------------------

        context["project"] = memory.get(
            "project",
            {},
        )

        context["style"] = memory.get(
            "style",
            {},
        )

        context["session"] = memory.get(
            "session",
            {},
        )

        # * ------------------------------------------
        # * Search relevant memory
        # * ------------------------------------------

        if (
            query
            and self.search is not None
        ):

            context["matches"] = self.search.search(
                query,
            )

        # * ------------------------------------------
        # * Recent edits
        # * ------------------------------------------

        edits = memory.get(
            "edits",
            [],
        )

        if isinstance(edits, list):

            context["edits"] = edits[-10:]

        # * ------------------------------------------
        # * Dependencies
        # * ------------------------------------------

        dependencies = memory.get(
            "dependencies",
            [],
        )

        if isinstance(dependencies, list):

            context["dependencies"] = dependencies

        return context

    # * --------------------------------------------------
    # * Summary
    # * --------------------------------------------------

    def summary(
        self,
        context: dict[str, Any],
    ) -> str:
        """
        Convert memory context into a compact
        text representation.
        """

        if not context:
            return ""

        lines = []

        project = context.get(
            "project",
            {},
        )

        if project:

            lines.append(
                f"Project: {project}"
            )

        style = context.get(
            "style",
            {},
        )

        if style:

            lines.append(
                f"Style: {style}"
            )

        session = context.get(
            "session",
            {},
        )

        if session:

            lines.append(
                f"Session: {session}"
            )

        matches = context.get(
            "matches",
            [],
        )

        if matches:

            lines.append(
                "Relevant Memory:"
            )

            for match in matches:

                lines.append(
                    f"- {match}"
                )

        return "\n".join(
            lines
        )