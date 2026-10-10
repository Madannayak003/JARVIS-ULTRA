"""
JARVIS PRO
News Skill

Explicit user-requested news is independent from
the automatic Morning Brief setting.

Morning Brief ON/OFF controls startup news only.
"""

from core.registry import register
from core.morning_brief import get_morning_brief


def get_news(data=None):

    print(
        "[NEWS] Explicit news request received."
    )

    try:

        result = get_morning_brief()

        if not result:

            return (
                "I couldn't retrieve the latest "
                "news right now."
            )

        return result

    except Exception as error:

        print(
            "[NEWS ERROR]",
            error,
        )

        return (
            "I couldn't retrieve the latest "
            "news right now."
        )


register(
    "get_news",
    get_news,
)