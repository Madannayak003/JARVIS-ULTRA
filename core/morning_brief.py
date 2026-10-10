"""
=============================================================
JARVIS PRO — MORNING BRIEF
=============================================================

Structured RSS-based startup news briefing.

This module:
    - Fetches current headlines from RSS feeds
    - Combines World, India, and Technology news
    - Removes duplicates
    - Returns a concise briefing

This module does NOT:
    - start TTS
    - start microphone
    - create another assistant
    - replace NCI
    - manage the HUD
    - manage shutdown
"""

from __future__ import annotations

import html
import re
import urllib.request
import xml.etree.ElementTree as ET

from concurrent.futures import ThreadPoolExecutor

from hud.bus import hud_bus
from hud.events import HUDEvent

# * =============================================================
# * CONFIGURATION
# * =============================================================

FEEDS = {
    "world": (
        "https://feeds.bbci.co.uk/news/world/rss.xml"
    ),

    "india": (
        "https://feeds.bbci.co.uk/news/world/"
        "asia/india/rss.xml"
    ),

    "technology": (
        "https://feeds.bbci.co.uk/news/"
        "technology/rss.xml"
    ),
}


REQUEST_TIMEOUT = 10

MAX_HEADLINES = 6

MAX_SPOKEN_HEADLINES = 3


# * =============================================================
# * INTERNAL HELPERS
# * =============================================================

def _clean_text(
    value: str,
) -> str:

    value = html.unescape(
        value or ""
    )

    value = re.sub(
        r"<[^>]+>",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


# * =============================================================
# * FETCH ONE RSS FEED
# * =============================================================

def _fetch_feed(
    category: str,
    url: str,
) -> list[dict[str, str]]:

    print(
        f"[MORNING BRIEF] Fetching {category} news..."
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "JARVIS-PRO/1.0 "
                "(RSS News Reader)"
            ),
            "Accept": (
                "application/rss+xml, "
                "application/xml, "
                "text/xml"
            ),
        },
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=REQUEST_TIMEOUT,
        ) as response:

            data = response.read()

    except Exception as error:

        print(
            "[MORNING BRIEF] "
            f"{category} feed failed: {error}"
        )

        return []

    try:

        root = ET.fromstring(
            data
        )

    except ET.ParseError as error:

        print(
            "[MORNING BRIEF] "
            f"{category} RSS parse failed: {error}"
        )

        return []

    results: list[dict[str, str]] = []

    for item in root.findall(
        ".//item"
    ):

        title_element = item.find(
            "title"
        )

        link_element = item.find(
            "link"
        )

        if title_element is None:

            continue

        title = _clean_text(
            title_element.text or ""
        )

        link = (
            _clean_text(
                link_element.text or ""
            )
            if link_element is not None
            else ""
        )

        if not title:

            continue

        results.append(
            {
                "category": category,
                "title": title,
                "link": link,
            }
        )

    print(
        "[MORNING BRIEF] "
        f"{category}: {len(results)} headlines"
    )

    return results


# * =============================================================
# * DUPLICATE FILTER
# * =============================================================

def _deduplicate(
    headlines: list[dict[str, str]],
) -> list[dict[str, str]]:

    unique: list[dict[str, str]] = []

    seen: set[str] = set()

    for item in headlines:

        normalized = re.sub(
            r"[^a-z0-9]+",
            " ",
            item["title"].lower(),
        ).strip()

        if not normalized:

            continue

        if normalized in seen:

            continue

        seen.add(
            normalized
        )

        unique.append(
            item
        )

    return unique


# * =============================================================
# * FETCH ALL NEWS
# * =============================================================

def fetch_news() -> list[dict[str, str]]:

    all_headlines: list[dict[str, str]] = []

    for category, url in FEEDS.items():

        headlines = _fetch_feed(
            category,
            url,
        )

        all_headlines.extend(
            headlines[:4]
        )

    return _deduplicate(
        all_headlines
    )


# * =============================================================
# * BUILD FULL BRIEF
# * =============================================================

def build_brief(
    headlines: list[dict[str, str]],
) -> str | None:

    if not headlines:

        return None

    selected = headlines[
        :MAX_HEADLINES
    ]

    lines = [
        "Here are today's top headlines."
    ]

    for index, item in enumerate(
        selected,
        start=1,
    ):

        category = (
            item["category"]
            .upper()
        )

        lines.append(
            f"{index}. "
            f"[{category}] "
            f"{item['title']}"
        )

    return "\n".join(
        lines
    )


# * =============================================================
# * BUILD SPOKEN BRIEF
# * =============================================================

def build_spoken_brief(
    headlines: list[dict[str, str]],
) -> str:

    if not headlines:

        return (
            "I couldn't retrieve the latest "
            "news right now."
        )

    selected = headlines[
        :MAX_SPOKEN_HEADLINES
    ]

    parts = [
        "Here are today's top news headlines."
    ]

    for item in selected:

        parts.append(
            item["title"]
        )

    return " ".join(
        parts
    )


# * =============================================================
# * HUD NEWS EVENT
# * =============================================================

def publish_to_hud(
    headlines: list[dict[str, str]],
) -> None:
    """
    Publish Morning Brief headlines through the existing
    JARVIS HUD event bus.
    """

    if not headlines:
        return

    try:

        hud_bus.publish(
            HUDEvent(
                name="morning_brief",
                data={
                    "headlines": headlines[
                        :MAX_HEADLINES
                    ],
                },
                source="morning_brief",
            )
        )

        print(
            "[MORNING BRIEF] "
            "News published to HUD."
        )

    except Exception as error:

        print(
            "[MORNING BRIEF] "
            f"HUD publish failed safely: {error}"
        )


# * =============================================================
# * PUBLIC API
# * =============================================================

def get_morning_brief() -> str | None:

    print(
        "[MORNING BRIEF] "
        "Fetching current top news..."
    )

    headlines = fetch_news()

    if not headlines:

        print(
            "[MORNING BRIEF] "
            "No headlines available."
        )

        return None

    print(
        "[MORNING BRIEF] "
        f"{len(headlines)} headlines ready."
    )

    publish_to_hud(
        headlines
    )

    return build_brief(
        headlines
    )


# * =============================================================
# * BACKGROUND FETCH
# * =============================================================

_executor = ThreadPoolExecutor(
    max_workers=1,
    thread_name_prefix="JARVIS-News",
)


def _fetch_news_for_startup():

    headlines = fetch_news()

    if headlines:

        publish_to_hud(
            headlines
        )

    return headlines


def start_news_fetch():

    print(
        "[MORNING BRIEF] "
        "Starting background news fetch..."
    )

    return _executor.submit(
        _fetch_news_for_startup
    )

# * =============================================================
# * SHUTDOWN
# * =============================================================

def shutdown():

    _executor.shutdown(
        wait=False,
        cancel_futures=True,
    )