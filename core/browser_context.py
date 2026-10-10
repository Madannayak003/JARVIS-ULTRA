"""
=============================================================
JARVIS PRO — BROWSER CONTEXT
=============================================================

Centralized runtime context for browser intelligence.

This module remembers browser-related information so that
higher-level JARVIS/NCI components can resolve references such
as:

    "open that"
    "open the second one"
    "play the first one"
    "search that again"
    "what am I watching?"

IMPORTANT:

This module does NOT:
    - control Playwright
    - execute browser actions
    - perform searches
    - call AI
    - modify NCI
    - dispatch commands

It only stores browser context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


# * =============================================================
# * BROWSER RESULT
# * =============================================================

@dataclass
class BrowserResult:

    title: str = ""

    url: str = ""

    platform: str = ""

    result_type: str = ""

    data: dict[str, Any] = field(
        default_factory=dict
    )


# * =============================================================
# * BROWSER CONTEXT
# * =============================================================

@dataclass
class BrowserContext:

    # * ---------------------------------------------------------
    # * Current browser state
    # * ---------------------------------------------------------

    current_url: str = ""

    current_site: str = ""

    current_title: str = ""

    current_tab: int = 0

    # * ---------------------------------------------------------
    # * Last search
    # * ---------------------------------------------------------

    last_search_query: str = ""

    last_search_platform: str = ""

    last_search_results: list[BrowserResult] = field(
        default_factory=list
    )

    # * ---------------------------------------------------------
    # * Current selection
    # * ---------------------------------------------------------

    selected_result: Optional[BrowserResult] = None

    selected_index: int = -1

    # * ---------------------------------------------------------
    # * YouTube
    # * ---------------------------------------------------------

    youtube_query: str = ""

    youtube_queue: list[BrowserResult] = field(
        default_factory=list
    )

    youtube_index: int = -1

    current_youtube_video: Optional[BrowserResult] = None

    # * =========================================================
    # * CURRENT PAGE
    # * =========================================================

    def set_page(
        self,
        url: str = "",
        site: str = "",
        title: str = "",
        tab: int = 0,
    ) -> None:

        self.current_url = str(url or "")

        self.current_site = str(site or "")

        self.current_title = str(title or "")

        self.current_tab = tab

    # * =========================================================
    # * SEARCH
    # * =========================================================

    def set_search(
        self,
        query: str,
        platform: str,
        results: list[dict[str, Any]] | list[BrowserResult],
    ) -> None:

        self.last_search_query = str(
            query or ""
        )

        self.last_search_platform = str(
            platform or ""
        )

        normalized: list[BrowserResult] = []

        for result in results:

            if isinstance(
                result,
                BrowserResult,
            ):

                normalized.append(
                    result
                )

            elif isinstance(
                result,
                dict,
            ):

                normalized.append(
                    BrowserResult(
                        title=str(
                            result.get(
                                "title",
                                "",
                            )
                        ),
                        url=str(
                            result.get(
                                "url",
                                "",
                            )
                        ),
                        platform=str(
                            result.get(
                                "platform",
                                platform,
                            )
                        ),
                        result_type=str(
                            result.get(
                                "result_type",
                                "",
                            )
                        ),
                        data=dict(result),
                    )
                )

        self.last_search_results = normalized

    # * =========================================================
    # * RESULT SELECTION
    # * =========================================================

    def select_result(
        self,
        index: int,
    ) -> Optional[BrowserResult]:

        if not self.last_search_results:

            self.selected_result = None

            self.selected_index = -1

            return None

        if index < 0:

            return None

        if index >= len(
            self.last_search_results
        ):

            return None

        self.selected_index = index

        self.selected_result = (
            self.last_search_results[index]
        )

        return self.selected_result

    # * =========================================================
    # * RESULT BY POSITION
    # * =========================================================

    def get_result(
        self,
        position: int,
    ) -> Optional[BrowserResult]:

        index = position - 1

        if index < 0:

            return None

        if index >= len(
            self.last_search_results
        ):

            return None

        return self.last_search_results[index]

    # * =========================================================
    # * YOUTUBE QUEUE
    # * =========================================================

    def set_youtube_queue(
        self,
        query: str,
        videos: list[dict[str, Any]] | list[BrowserResult],
    ) -> None:

        self.youtube_query = str(
            query or ""
        )

        normalized: list[BrowserResult] = []

        for video in videos:

            if isinstance(
                video,
                BrowserResult,
            ):

                normalized.append(
                    video
                )

            elif isinstance(
                video,
                dict,
            ):

                normalized.append(
                    BrowserResult(
                        title=str(
                            video.get(
                                "title",
                                "",
                            )
                        ),
                        url=str(
                            video.get(
                                "url",
                                "",
                            )
                        ),
                        platform="youtube",
                        result_type="video",
                        data=dict(video),
                    )
                )

        self.youtube_queue = normalized

        self.youtube_index = (
            0 if normalized else -1
        )

        self.current_youtube_video = (
            normalized[0]
            if normalized
            else None
        )

    # * =========================================================
    # * YOUTUBE POSITION
    # * =========================================================

    def get_youtube_video(
        self,
        position: int,
    ) -> Optional[BrowserResult]:

        index = position - 1

        if index < 0:

            return None

        if index >= len(
            self.youtube_queue
        ):

            return None

        return self.youtube_queue[index]

    # * =========================================================
    # * CURRENT YOUTUBE VIDEO
    # * =========================================================

    def set_current_youtube(
        self,
        index: int,
    ) -> Optional[BrowserResult]:

        if index < 0:

            return None

        if index >= len(
            self.youtube_queue
        ):

            return None

        self.youtube_index = index

        self.current_youtube_video = (
            self.youtube_queue[index]
        )

        return self.current_youtube_video

    # * =========================================================
    # * CLEAR
    # * =========================================================

    def clear_search(self) -> None:

        self.last_search_query = ""

        self.last_search_platform = ""

        self.last_search_results = []

        self.selected_result = None

        self.selected_index = -1

    def search_snapshot(self) -> dict[str, Any]:
        """Return search state without mixing it with current page state."""
        return {
            "query": self.last_search_query,
            "platform": self.last_search_platform,
            "results": [
                {
                    "position": index,
                    "title": result.title,
                    "url": result.url,
                    "platform": result.platform,
                    "result_type": result.result_type,
                    "data": dict(result.data),
                }
                for index, result in enumerate(self.last_search_results, 1)
            ],
        }

    # * =========================================================
    # * SNAPSHOT
    # * =========================================================

    def snapshot(self) -> dict[str, Any]:

        return {

            "current_url":
                self.current_url,

            "current_site":
                self.current_site,

            "current_title":
                self.current_title,

            "current_tab":
                self.current_tab,

            "last_search_query":
                self.last_search_query,

            "last_search_platform":
                self.last_search_platform,

            "last_search_results":
                [
                    result.data
                    for result
                    in self.last_search_results
                ],

            "selected_index":
                self.selected_index,

            "selected_result":
                (
                    self.selected_result.data
                    if self.selected_result
                    else None
                ),

            "youtube_query":
                self.youtube_query,

            "youtube_index":
                self.youtube_index,

            "youtube_queue":
                [
                    video.data
                    for video
                    in self.youtube_queue
                ],

            "current_youtube_video":
                (
                    self.current_youtube_video.data
                    if self.current_youtube_video
                    else None
                ),
        }


# * =============================================================
# * GLOBAL RUNTIME CONTEXT
# * =============================================================

browser_context = BrowserContext()
