"""
=============================================================
JARVIS PRO — BROWSER REFERENCE RESOLVER
=============================================================

Resolves conversational references against the centralized
BrowserContext.

This module does NOT:
    - control Playwright
    - execute browser actions
    - call AI
    - modify NCI
    - dispatch commands

It only resolves references.
"""

from __future__ import annotations

from typing import Optional

from .browser_context import (
    BrowserContext,
    BrowserResult,
    browser_context,
)


# * =============================================================
# * BROWSER REFERENCE RESOLVER
# * =============================================================

class BrowserReferenceResolver:

    def __init__(
        self,
        context: BrowserContext | None = None,
    ):

        self.context = (
            context
            if context is not None
            else browser_context
        )

    # * =========================================================
    # * POSITIONAL RESULT
    # * =========================================================

    def result(
        self,
        position: int,
    ) -> Optional[BrowserResult]:

        return self.context.get_result(
            position
        )
        
    # * =========================================================
    # * RESOLVE POSITIONAL REFERENCE
    # * =========================================================

    def resolve_position(
        self,
        position: int,
    ) -> Optional[BrowserResult]:

        return self.context.get_result(
            position
        )
        
    # * =========================================================
    # * RESOLVE NCI REFERENCE
    # * =========================================================

    def resolve_reference(
        self,
        reference: str,
    ) -> Optional[BrowserResult]:

        from brain.conversation_understanding import (
            conversation_understanding,
        )

        position = (
            conversation_understanding.reference_position(
                reference
            )
        )

        if position is None:

            return None

        return self.resolve_position(
            position
        )

    # * =========================================================
    # * SELECT RESULT
    # * =========================================================

    def select(
        self,
        position: int,
    ) -> Optional[BrowserResult]:

        result = self.context.get_result(
            position
        )

        if result is None:

            return None

        return self.context.select_result(
            position - 1
        )

    # * =========================================================
    # * CURRENT SELECTED RESULT
    # * =========================================================

    def selected(
        self,
    ) -> Optional[BrowserResult]:

        return self.context.selected_result

    # * =========================================================
    # * YOUTUBE POSITION
    # * =========================================================

    def youtube(
        self,
        position: int,
    ) -> Optional[BrowserResult]:

        return self.context.get_youtube_video(
            position
        )

    # * =========================================================
    # * CURRENT YOUTUBE VIDEO
    # * =========================================================

    def current_youtube(
        self,
    ) -> Optional[BrowserResult]:

        return (
            self.context.current_youtube_video
        )

    # * =========================================================
    # * PREVIOUS YOUTUBE VIDEO
    # * =========================================================

    def previous_youtube(
        self,
    ) -> Optional[BrowserResult]:

        index = (
            self.context.youtube_index
            - 1
        )

        if index < 0:

            return None

        return self.context.youtube_queue[
            index
        ]

    # * =========================================================
    # * NEXT YOUTUBE VIDEO
    # * =========================================================

    def next_youtube(
        self,
    ) -> Optional[BrowserResult]:

        index = (
            self.context.youtube_index
            + 1
        )

        if index >= len(
            self.context.youtube_queue
        ):

            return None

        return self.context.youtube_queue[
            index
        ]


# * =============================================================
# * GLOBAL RESOLVER
# * =============================================================

browser_reference_resolver = (
    BrowserReferenceResolver()
)